import click
from distutils.spawn import find_executable
import yaml
import os
import subprocess
from uuid import uuid4
import shutil
import requests
import tarfile
import json

walkoff_charts_repo = 'https://nsacyber.github.io/Walkoff/charts'


@click.command()
@click.option('-o', '--out', help='Path to the output directory')
@click.option('--platform', default='linux_x86_64', help='Target platform for walkoffctl')
@click.option('--python-version', help='Python version to target for walkoffctl', type=click.Choice(['2', '3']), default='3')
@click.option('--walkoff-version', default='latest')
@click.option('--helm-archive', help='Path to Helm archive', required=True)
@click.pass_context
def download(ctx, out, platform, python_version, walkoff_version, images, helm_archive):
    """Downloads Walkoff for offline installation
    """
    if python_version == '2':
        python_version = '27'
    os.makedirs(out)
    download_get_pip(out)
    download_walkoff_and_deps(out, python_version, platform)
    verify_helm(ctx)
    copy_helm(helm_archive, out)
    download_charts(out, walkoff_version)
    download_docker_images(images, out)
    compress_repo(out)


def download_get_pip(out):
    resp = requests.get('https://bootstrap.pypa.io/get-pip.py')
    with open(os.path.join(out, 'get-pip.py')) as get_pip:
        get_pip.write(resp.text)




def download_walkoff_and_deps(directory, version, platform):
    click.echo('Downloading Python Dependencies...')
    dest = os.path.join(directory, 'pythondeps')
    subprocess.call(['pip', 'download', '--platform', platform, '--python-version', version, '-d', dest, 'walkoff'])
    subprocess.call(['pip', 'download', '--platform', platform, '--python-version', version, '-d', dest, 'pip'])


def verify_helm(ctx):
    if not find_executable('helm'):
        click.echo('Helm must be installed to complete packaging. '
                   'See https://docs.helm.sh/using_helm/#installing-helm for instructions.')
        click.echo('If installing without kubernetes, run "helm init --client-only" after installing')
        ctx.exit(1)


def download_charts(base_dir, walkoff_version):
    click.echo('Downloading Helm Charts...')
    subprocess.call(['helm', 'repo', 'add', 'walkoff', walkoff_charts_repo])
    subprocess.call(['helm', 'update'])
    out_dir = os.path.join(base_dir, 'charts')
    cmd = 'helm fetch --untar --untardir {}'.format(out_dir)
    if walkoff_version:
        cmd += ' --version {}'.format(walkoff_version)
    cmd += ' walkoff walkoff'
    call(cmd)
    download_recursive(base_dir, 'walkoff', walkoff_charts_repo)


def download_docker_images(src, base_dir):
    click.echo('Download Docker Images...')
    docker_path = os.path.join(base_dir, 'images')
    charts_path = os.path.join(base_dir, 'charts')
    os.makedirs(docker_path)
    with open(os.path.join('.', 'data', 'chart_images_paths.json')) as chart_image_paths:
        chart_image_paths = json.load(chart_image_paths.read())
    for chart, paths in chart_image_paths.items():
        with open(os.path.join(charts_path, chart, 'values.yaml')) as chart_values:
            chart_values = yaml.safe_load(chart_values)
            for image_path in paths:
                repo_path = image_path['repository'].split('.')
                tag_path = image_path['tag'].split('.')
                repo = get_element(chart_values, repo_path)
                output_file = os.path.join(docker_path, '{}.tar'.format(repo))
                tag = get_element(chart_values, tag_path)
                call('docker save -o {} {}:{}'.format(output_file, repo, tag))


def get_element(yaml, path):
    current = yaml
    for elem in path:
        current = yaml[elem]
    return current


def copy_helm(src, base_dir):
    click.echo('Copying Helm Binary...')
    helm_path = os.path.join(base_dir, 'helm.tgz')
    shutil.copy(src, helm_path)


def compress_repo(out):
    click.echo('Compressing...')
    tar = tarfile.TarFile('{}.tgz'.format(out), mode='w')
    tar.add(out)
    tar.c


def call(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p.stdout.read())
    print(p.stderr.read())


def extract_deps(base, chart_dir):
    req = os.path.join(base, chart_dir, 'requirements.yaml')
    if os.path.isfile(req):
        with open(req) as f:
            data = yaml.load(f)
            return data['dependencies']
    print('No requirements found for {}'.format(chart_dir))
    return []


def get_new_repos(existing, deps):
    return {dep['repository'] for dep in deps} - set(existing.keys())


def add_repos(new_repos, existing_repos):
    for repo in new_repos:
        name = uuid4()
        print('adding repo {} as {}'.format(repo, name))
        call('helm repo add {} {}'.format(name, repo))
        existing_repos[repo] = name
    call('helm update')


def get_repo_name(repos, target):
    if target not in repos:
        if target[:-1] in repos:
            return target[:-1]
        else:
            raise ValueError('DONE FUcked Up')
    return target


def download_new_charts(existing, repos, deps, base_dir):
    new_charts = []
    for dep in deps:
        print(dep)
        name = dep['name']
        if name not in existing:
            repo = get_repo_name(repos, dep['repository'])
            out_dir = os.path.join(base_dir, name)
            command = 'helm fetch --untar --untardir {} --version {} {}/{}'.format(out_dir, dep['version'], repos[repo], name)
            print(command)
            call(command)
            new_charts.append((name, repo))
    return new_charts


def get_repo_names():
    out = subprocess.Popen('helm repo list', stdout=subprocess.PIPE)
    repos = {}
    for line in out.stdout.read().split('\n')[1:]:
        line = [x.strip() for x in line.split('\t')]
        if len(line) == 2:
            repos[line[1]] = line[0]
    print('repos: {}'.format(repos))
    return repos


def download_recursive(base_dir, chart, repo):
    repos = get_repo_names()
    charts = [(chart, repo)]
    seen_charts = set(charts)
    while charts:
        chart, repo = charts.pop()
        print('DOWNLOADNG FOR {} from {}'.format(chart, repo))
        deps = extract_deps(base_dir, chart)
        new_repos = get_new_repos(repos, deps)
        print('Need to add repos {}'.format(new_repos))
        add_repos(new_repos, repos)
        repos = get_repo_names()
        new_charts = download_new_charts(seen_charts, repos, deps, base_dir)
        charts.extend(new_charts)
    print('DONE!')

