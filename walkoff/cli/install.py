import click
import subprocess
from distutils.spawn import find_executable
import requests
import os
import stat
import tarfile
import shutil
import yaml
from base64 import b64encode

from kubernetes import client, config
from OpenSSL import crypto, SSL


@click.command()
@click.pass_context
@click.option('-a', '--archive', help='Archived installation for off-line installation')
@click.option('-v', '--values', help='Path to a Helm chart values YAML to use in the installation')
def install(ctx, archive, values):
    """ Installs Walkoff in a kubernetes cluster.

    If installing on kubernetes, Walkoff will use Helm to install itself onto the kubernetes cluster
    """
    #TODO Check if values exists
    #install pip from get-pip if necessary python get-pip.py --no-index --find-links=/local/copies
    if archive:
        offline_install(ctx, values)
    else:
        online_install(ctx, values)


def offline_install(ctx, values):
    #TODO: Offline install must execute separate script to install wlkoffctl
    if not find_executable('helm'):
        install_helm_offline(ctx)
    setup_helm()
    add_charts_offline()
    install_docker_repository()
    populate_docker_repository()
    if not values:
        values = get_chart_configuration()
    install_walkoff(values)


def helm_command(args, tiller, namespace):
    cmd = ['helm'] + args + ['--tiller-namespace', tiller, '--namespace', namespace]
    try:
        r = subprocess.check_output(cmd)
        print(r.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        click.echo('Helm returned error code {}: {}'.format(e.returncode, e.output.decode('utf-8')))


def kubectl_command(args, namespace):
    cmd = ['kubectl'] + args
    if namespace is not None:
        cmd += ['--namespace', namespace]
    try:
        r = subprocess.check_output(cmd)
        print(r.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        click.echo('Kubectl returned error code {}: {}'.format(e.returncode, e.output.decode('utf-8')))


def online_install(ctx, values):
    click.echo('Installing WALKOFF to Kubernetes cluster. Online install.')
    k8s_api = None
    k8s_custom_api = None
    try:
        config_dir = os.environ.get('KUBECONFIG', os.path.join(os.path.expanduser("~"), ".kube", "config"))
        config_dir = click.prompt("Enter location of kubernetes config", 
                                  default=config_dir)

        contexts, current = config.list_kube_config_contexts(config_file=config_dir)
        contexts = [context["name"] for context in contexts]
        current = current["name"]

        context = click.prompt("Available contexts: {}\nEnter context to install WALKOFF to (current/default: {}): ".format(contexts, current), 
                               default=current)

        config.load_kube_config(config_file=config_dir, context=context)
        k8s_api = client.CoreV1Api()
        k8s_custom_api = client.CustomObjectsApi()
    except IOError as e:
        print("Could not open config: {}".format(e))

    namespaces = k8s_api.list_namespace()
    namespaces = [ns.metadata.name for ns in namespaces.items]
    namespace = click.prompt("Available namespaces: {}\nEnter namespace to install WALKOFF in (default: default)".format(namespaces),
                             default="default")

    if namespace not in namespaces:
        if click.confirm("{} does not exist - do you want to create it now?"):
            new_namespace = client.V1Namespace(metadata={'name': namespace})
            k8s_api.create_namespace(new_namespace)

    tiller_namespace = click.prompt('Enter the namespace your Tiller service resides in (default: kube-system): ',
                                    default='kube-system')

    click.echo("Generating ZMQ certificates for WALKOFF.")
    subprocess.call(['python', 'scripts/generate_certificates.py'])
    click.echo("Adding ZMQ certificates to Kubernetes secrets.")
    kubectl_command(['create', 'secret', 'generic', 'walkoff-zmq-private-keys',
                     '--from-file=server.key_secret=./.certificates/private_keys/server.key_secret',
                     '--from-file=client.key_secret=./.certificates/private_keys/client.key_secret'],
                    namespace)

    kubectl_command(['create', 'secret', 'generic', 'walkoff-zmq-public-keys',
                     '--from-file=server.key=./.certificates/public_keys/server.key',
                     '--from-file=client.key=./.certificates/public_keys/client.key'],
                    namespace)

    existing_secrets = k8s_api.list_namespaced_secret(namespace)
    redis_secret_name = None
    redis_hostname = None
    if click.confirm('Is there an existing Redis instance WALKOFF should use?'):
        redis_hostname = click.prompt('Enter the Redis hostname (if it is not in the same Kubernetes namespace as WALKOFF, enter a fully qualified domain name)')
        if click.confirm("Is the Redis password already stored in a Kubernetes secret?"):
            redis_secret_name = click.prompt('Available secrets: {}\nEnter the name of the secret the Redis password is stored in with a key of "redis-password" (leave blank for none): ', default="")
            if redis_secret_name not in existing_secrets:
                redis_secret_name = None
                click.echo('No secret with that name in this namespace. Creating a new secret to store password.')

    if not redis_secret_name:
        redis_secret_name = "walkoff-redis-secret"
        new_pass = click.prompt('Enter a password for the Redis instance', hide_input=True, confirmation_prompt=True)
        redis_secret_obj = client.V1Secret(metadata={'name': redis_secret_name}, data={'redis-password': b64encode(new_pass.encode('utf-8')).decode('utf-8')})
        k8s_api.create_namespaced_secret(namespace, redis_secret_obj)

    if not redis_hostname:
        redis_hostname = 'walkoff-redis'
        helm_command(['install', 'stable/redis',
                      '--name', redis_hostname,
                      '--values', 'walkoff/cli/setupfiles/redis-helm-values.yaml',
                      '--set', 'existingSecret={}'.format(redis_secret_name)],
                     tiller_namespace, namespace)
        

    with open("walkoff/cli/setupfiles/redis-helm-values.yaml", 'r+') as f:
        try:
            y = yaml.load(f)
            y['existingSecret'] = redis_secret_name
            f.seek(0)
            f.truncate()
            yaml.dump(y, f, default_flow_style=False)
        except yaml.YAMLError as e:
            click.echo("Error reading redis-helm-values.yaml")

    execution_secret_name = None
    execution_db_hostname = None
    if click.confirm('Do you have an existing PostgreSQL database to store WALKOFF execution data in?'):
        execution_db_hostname = click.prompt('Enter the database hostname (if it is not in the same Kubernetes namespace as WALKOFF, enter a fully qualified domain name)')
        if click.confirm("Is the PostgreSQL password already stored in a Kubernetes secret?"):
            execution_secret_name = click.prompt('Available secrets: {}\nEnter the name of the secret the PostgreSQL password is stored in with a key of "postgres-password" (leave blank for none): ', default="")
            if execution_secret_name not in existing_secrets:
                execution_secret_name = None
                click.echo('No secret with that name in this namespace. Creating a new secret to store password.')

    if not execution_secret_name:
        execution_secret_name = "walkoff-postgres-execution-secret"
        new_pass = click.prompt('Enter a password for the PostgreSQL instance', hide_input=True, confirmation_prompt=True)
        execution_secret_obj = client.V1Secret(metadata={'name': execution_secret_name}, data={'postgres-password': b64encode(new_pass.encode('utf-8')).decode('utf-8')})
        k8s_api.create_namespaced_secret(namespace, execution_secret_obj)

    with open("walkoff/cli/setupfiles/execution-postgres-helm-values.yaml", 'r+') as f:
        try:
            y = yaml.load(f)
            y['existingSecret'] = execution_secret_name
            f.seek(0)
            f.truncate()
            yaml.dump(y, f, default_flow_style=False)
        except yaml.YAMLError as e:
            click.echo("Error reading redis-helm-values.yaml")

    if not execution_db_hostname:
        helm_command(['install', 'stable/postgresql',
                     '--name', 'execution-db',
                     '--values', 'walkoff/cli/setupfiles/execution-postgres-helm-values.yaml'],
                     tiller_namespace, namespace)

    walkoff_db_secret_name = None
    walkoff_db_hostname = None
    if click.confirm('Do you have an existing PostgreSQL database to store WALKOFF application data in? (This can be the same or different as the previous)'):
        walkoff_db_hostname = click.prompt('Enter the database hostname (if it is not in the same Kubernetes namespace as WALKOFF, enter a fully qualified domain name)')
        if click.confirm("Is the PostgreSQL password already stored in a Kubernetes secret?"):
            walkoff_db_secret_name = click.prompt('Available secrets: {}\nEnter the name of the secret the PostgreSQL password is stored in with a key of "postgres-password" (leave blank for none): ', default="")
            if walkoff_db_secret_name not in existing_secrets:
                walkoff_db_secret_name = None
                click.echo('No secret with that name in this namespace. Creating a new secret to store password.')

    if not walkoff_db_secret_name:
        walkoff_db_secret_name = "walkoff-postgres-secret"
        new_pass = click.prompt('Enter a password for the PostgreSQL instance', hide_input=True, confirmation_prompt=True)
        walkoff_db_secret_obj = client.V1Secret(metadata={'name': walkoff_db_secret_name}, data={'postgres-password': b64encode(new_pass.encode('utf-8')).decode('utf-8')})
        k8s_api.create_namespaced_secret(namespace, walkoff_db_secret_obj)

    with open("walkoff/cli/setupfiles/walkoff-postgres-helm-values.yaml", 'r+') as f:
        try:
            y = yaml.load(f)
            y['existingSecret'] = walkoff_db_secret_name
            f.seek(0)
            f.truncate()
            yaml.dump(y, f, default_flow_style=False)
        except yaml.YAMLError as e:
            click.echo("Error reading redis-helm-values.yaml")

    if not walkoff_db_hostname:
        helm_command(['install', 'stable/postgresql',
                     '--name', 'walkoff-db',
                     '--values', 'walkoff/cli/setupfiles/walkoff-postgres-helm-values.yaml'],
                     tiller_namespace, namespace)

    ca_secret_name = None
    if click.confirm('Do you have an existing CA signing key pair stored in Kubernetes secrets?'):
        ca_secret_name = click.prompt('Available secrets: {}\nEnter the name of the secret the key pair is stored in (leave blank for none): ', default="")
        if ca_secret_name not in existing_secrets:
            ca_secret_name = None
            click.echo('No secret with that name in this namespace. Creating a new secret to store password.')

    if not ca_secret_name:
        crt = None
        key = None
        if click.confirm('Do you have existing CA signing key pair files?'):
            while not crt:
                crt = click.prompt('Enter the path to a cert (.crt) file: ')
                try:
                    with open(crt, 'rb') as f:
                        crt = b64encode(f.read()).decode('ascii')
                        click.echo('Successfully loaded cert')
                except IOError as e:
                    click.echo('Error reading {}: {}'.format(crt, e))
                    crt = None

            while not key:
                key = click.prompt('Enter the path to the matching private key (.key) file: ')
                try:
                    with open(key, 'rb') as f:
                        key = b64encode(f.read()).decode('ascii')
                        click.echo('Successfully loaded key.')
                except IOError as e:
                    click.echo('Error reading {}: {}'.format(key, e))
                    key = None       
        else:
            key_obj = crypto.PKey()
            key_obj.generate_key(crypto.TYPE_RSA, 1024)

            cert = crypto.X509()
            cert.get_subject().CN = "walkoff"
            cert.set_serial_number(1)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key_obj)
            cert.sign(key_obj, 'sha256')

            with open('ca.crt', 'wb') as f:
                byte_cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
                crt = b64encode(byte_cert).decode('ascii')
                f.write(byte_cert)
            with open('ca.key', 'wb') as f:
                byte_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key_obj)
                key = b64encode(byte_key).decode('ascii')
                f.write(byte_key)

        tls_secret = client.V1Secret(metadata={'name': 'walkoff-ca-key-pair'}, data={'ca.crt': crt, 'ca.key': key}, type='kubernetes.io/tls')
        k8s_api.create_namespaced_secret('default', tls_secret) 

    helm_command(['install', 'stable/cert-manager',
                 '--name', 'walkoff-cert-manager'],
                 tiller_namespace, namespace)
                
    with open("walkoff/cli/setupfiles/cert.yaml", 'r+') as f:
        try:
            y = yaml.load(f)
            y['spec']['secretName'] = ca_secret_name
            f.seek(0)
            f.truncate()
            yaml.dump(y, f, default_flow_style=False)
        except yaml.YAMLError as e:
            click.echo("Error reading redis-helm-values.yaml")

    kubectl_command(['apply', '-f', 'walkoff/cli/setupfiles/cert-issuer.yaml'],
                    namespace)
    kubectl_command(['apply', '-f', 'walkoff/cli/setupfiles/cert.yaml'],
                    namespace)

    with open("walkoff/cli/setupfiles/walkoff-values.yaml", 'r+') as f:
        try:
            y = yaml.load(f)
            y['namespace'] = namespace
            y['resources']['redis']['service_name'] = redis_hostname
            y['resources']['redis']['secret_name'] = redis_secret_name
            y['resources']['execution_db']['service_name'] = execution_db_hostname
            y['resources']['execution_db']['secret_name'] = execution_secret_name
            y['resources']['walkoff_db']['service_name'] = walkoff_db_hostname
            y['resources']['walkoff_db']['secret_name'] = walkoff_db_secret_name
            f.seek(0)
            f.truncate()
            yaml.dump(y, f, default_flow_style=False)
        except yaml.YAMLError as e:
            click.echo("Error reading walkoff-values.yaml")

    helm_command(['install', './walkoff',
                  '--name', 'walkoff-deployment'],
                  tiller_namespace, namespace)
                 
    helm_command(['install', 'stable/docker-registry',
                  '--name', 'walkoff-docker-registry'],
                  tiller_namespace, namespace)

# https://github.com/helm/charts/blob/master/stable/docker-registry/README.md


def install_helm_online(ctx):
    click.echo('Helm not found. Installing... ')
    response = requests.get('https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get')
    if response.status_code == 200:
        with open('get_helm.sh') as f:
            f.write(response.text)
        os.chmod('get_helm.sh', stat.S_IXUSR)
        subprocess.call(['get_helm.sh'])
    else:
        click.echo("Could not connect to Helm's GitHub to retrieve script")
        ctx.exit(1)
    verify_helm_exists(ctx)


def install_helm_offline(ctx):
    click.echo('Helm not found. Installing...')
    archive = tarfile.open('./helm.tgz')
    archive.extractall('./helm')
    os.rename('./helm/helm', '/usr/local/bin/helm')
    verify_helm_exists(ctx)


def verify_helm_exists(ctx):
    if not find_executable('helm'):
        click.echo(
            'Could not install Helm. Please see https://docs.helm.sh/using_helm/#installing-helm for more information.')
        ctx.exit(1)


def setup_helm():
    click.echo('setting up Helm with proper TLS, RBAC')


def add_charts_online():
    click.echo('Downloading charts')


def add_charts_offline():
    click.echo('Adding charts offline using helm repo add <name> <URL>')


def get_chart_configuration():
    click.echo('launching interactive prompt to get configuration')


def install_walkoff(values):
    click.echo('Installing walkoff with {}')


def install_docker_repository():
    pass


def populate_docker_repository():
    pass

def generate_tls_keys():
    pass