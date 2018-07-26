import click
import os

from .update import commands as update_commands
from .install import install as install_command
from .status import status
from .local import commands as local_commands
from .dev import commands as dev_commands
from .local.util import load_config
from .deploy import commands as deploy_commands

# from kubernetes import client, config as kube_config


@click.group()
@click.option('-v', '--verbose', count=True, help='Specify the verbosity of the output')
@click.pass_context
def cli(ctx, verbose):
    """Command line controller for Walkoff
    """
    ctx.obj['verbose'] = verbose


@cli.command()
def version():
    """ Prints the version of Walkoff installed.
    """
    import walkoff
    click.echo('Walkoff v{}'.format(walkoff.__version__))


@cli.group()
@click.pass_context
def update(ctx):
    """ Updates Walkoff to the next version.

    Uses the main Git repository to update Walkoff to the most recent version.
    """
    pass


@cli.group()
@click.option('-d', '--dir', help='The directory of the Walkoff installation')
@click.pass_context
def local(ctx, dir):
    """Controls local installations of Walkoff
    """
    import walkoff.config
    dir = dir or os.getcwd()
    load_config(dir)
    ctx.obj['config'] = walkoff.config.Config
    ctx.obj['dir'] = dir


@cli.group()
@click.pass_context
def dev(ctx):
    """Functions useful for developing Walkoff
    """
    import walkoff.config
    load_config(os.getcwd())
    ctx.obj['config'] = walkoff.config.Config
    ctx.obj['dir'] = os.getcwd()


@cli.command()
@click.option('--from-local', is_flag=True, help='Prepare the current local installation for on-prem kubernetes')
@click.option('-d', '--dir', help='Path to the output directory')
@click.option('-a', '--apps', help='Comma-separated list of apps to download')
@click.option('-i', '-interfaces', help='Comma-separated list of interfaces to download')
@click.option('-ag', '--app-repo', help='Git repository for the apps')
@click.option('-ig', '--interface-repo', help='Git repository for the interfaces')
@click.option('--compress/--no-compress', default=True, help='Compress the resulting directory')
@click.pass_context
def download(ctx, dir, apps, app_repo, interface_repo, compress):
    """Downloads Walkoff for offline installation
    """

    if ctx.invoked_subcommand is None:
        click.echo('Downloading required files for Walkoff on-prem install')


@cli.group()
@click.pass_context
def deploy(ctx, app_repo, interface_repo):
    pass


command_groups = {
    cli: [install_command, status, version, download],
    update: update_commands,
    local: local_commands,
    dev: dev_commands,
    deploy: deploy_commands
}


def add_commands():
    for command_group, commands in command_groups.items():
        for command in commands:
            command_group.add_command(command)