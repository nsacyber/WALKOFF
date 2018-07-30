import click
import subprocess
from distutils.spawn import find_executable
import requests
import os
import stat
import tarfile


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


def online_install(ctx, values):
    click.echo('Installing Walkoff into kubernetes online')
    subprocess.call(['pip', 'install', 'walkoff'])
    if not find_executable('helm'):
        install_helm_online(ctx)
    setup_helm()
    add_charts_online()
    if not values:
        values = get_chart_configuration()
    install_walkoff(values)


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

