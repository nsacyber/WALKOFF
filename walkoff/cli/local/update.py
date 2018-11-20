import ctypes as cts
import os
import shutil
import subprocess
import time

import click
from git import Repo


@click.command()
@click.pass_context
@click.option('--check', help='Check if updates are available', is_flag=True)
@click.option('-b', '--backup', help='Create a backup of the entire walkoff directory')
@click.option('-bp', '--backup-path', help='The directory to which the backup should be stored', default='./backup')
@click.option('-v', '--version', help='Target version. If unspecified updates to the latest version')
def update(ctx, check, backup, backup_path):
    """Updates Walkoff to the most recent version

    Warning: Success of this operation is not guaranteed or necessarily reversible.
    """
    # click.echo('Updating Walkoff locally')
    walkoff_dir = ctx.obj['dir']
    os.chdir(walkoff_dir)
    latest_version = check_for_updates(ctx)
    if check:
        ctx.exit(0)

    if not is_admin():
        if not click.confirm(
                'Migrating databases and installing any new requirements might require admin privileges, but current '
                'user is not admin. Would you like to try anyways?'):
            ctx.exit(1)

    if backup:
        backup(backup_path)

    git_pull()
    clean_pycache(walkoff_dir, ctx.obj['verbose'])
    migrate_apps()
    migrate_databases()


def check_for_updates(ctx):
    r = Repo('.')
    current_tag = get_current_tag_name(r)
    r.git.fetch()
    r = Repo('.')
    latest_tag = get_current_tag_name(r)
    if current_tag == latest_tag:
        click.echo('Walkoff is up to date')
        ctx.exit(0)
    else:
        click.echo("Current version is {}. Latest version is {}".format(current_tag, latest_tag))
    return latest_tag


def get_current_tag_name(repo):
    return repo.tags[-1].path.split('/')[-1]


def is_admin():
    if os.name == 'posix':
        return os.geteuid() == 0
    elif os.name == 'nt':
        return cts.windll.shell32.IsUserAnAdmin() == 0
    else:
        raise ValueError('Unsupported OS: {}'.format(os.name))


def backup(backup_path):
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    from walkoff import __version__
    filename = '{}-{}'.format(__version__, time.strftime("%Y%m%d-%H%M%S"))
    path = os.path.join(backup_path, filename)
    if os.name == "nt":
        ext = "zip"
    elif os.name == "posix":
        ext = "gztar"
    else:
        raise ValueError('Unsupported OS {}'.format(os.name))

    click.echo("Creating {} backup archive... (This might take a while)".format(ext))
    shutil.make_archive(path, ext)
    click.echo("Backup created at {}".format(path))


def git_pull():
    click.echo("Pulling from current branch: ")
    click.echo(subprocess.check_output(["git", "branch"], stderr=subprocess.STDOUT, universal_newlines=True))
    click.echo(subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT, universal_newlines=True))


def clean_pycache(path=None, verbose=False):
    if path is None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        my_dir = os.path.dirname(os.path.abspath(path))

    for root, dirnames, filenames in os.walk(my_dir):
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                if verbose:
                    click.echo("Removing: " + os.path.join(root, filename))
                os.remove(os.path.join(root, filename))


def migrate_apps():
    # TODO: This needs serious effort. It needs to work like migrate workflows
    click.echo("Migrate apps has not yet been implemented.")


def migrate_databases():
    names = ["execution", "walkoff"]
    for name in names:
        try:
            r = (subprocess.check_output(["alembic", "--name", name, "current"], stderr=subprocess.STDOUT,
                                         universal_newlines=True))
            if "(head)" in r:
                click.echo("Already up to date, no alembic upgrade needed.")
            else:
                click.echo(subprocess.check_output(["alembic", "--name", name, "upgrade", "head"],
                                                   stderr=subprocess.STDOUT, universal_newlines=True))
        except subprocess.CalledProcessError:
            click.echo("Alembic encountered an error.")
            click.echo("Try manually running 'alembic --name {} upgrade head".format(name))
            click.echo("You may already be on the latest revision.")
            continue
