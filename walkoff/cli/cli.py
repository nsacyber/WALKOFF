import os

import click

from .deploy import commands as deploy_commands
from .dev import commands as dev_commands
from .install import install as install_command
from .install import uninstall as uninstall_command
from .local import commands as local_commands
from .local.util import load_config
from .status import status
from .update import commands as update_commands


# from kubernetes import client, config as kube_config


@click.group()
@click.option('-v', '--verbose', count=True, help='Specify the verbosity of the output')
@click.pass_context
def cli(ctx, verbose):
    """
    walkoffctl is a CLI tool for managing WALKOFF installations, locally and on Kubernetes clusters.
    """
    ctx.obj['verbose'] = verbose


@cli.command()
def version():
    """
    Displays the WALKOFF version currently in use.
    """
    import walkoff
    click.echo('Walkoff v{}'.format(walkoff.__version__))


@cli.group()
@click.pass_context
def update(ctx):
    """
    WIP - Updates WALKOFF on a Kubernetes cluster to the next version.
    """
    pass


@cli.group()
@click.option('-d', '--dir', help='The directory of the Walkoff installation')
@click.option('-c', '--config', help='The configuration file of the Walkoff installation')
@click.pass_context
def local(ctx, dir, config):
    """
    Commands for controlling local installations of WALKOFF.
    """
    if dir and config:
        click.echo('Cannot specify both dir and config options.')
        ctx.exit(1)
    if ctx.invoked_subcommand != 'install':
        import walkoff.config
        directory = config or dir or os.getcwd()
        load_config(directory)
        ctx.obj['config'] = walkoff.config.Config
        ctx.obj['dir'] = directory


@cli.group()
@click.pass_context
def dev(ctx):
    """
    Commands for assisting with development of WALKOFF.
    """
    import walkoff.config
    load_config(os.getcwd())
    ctx.obj['config'] = walkoff.config.Config
    ctx.obj['dir'] = os.getcwd()


@cli.group()
@click.pass_context
def deploy(ctx):
    """
    WIP - Commands for deploying apps and interfaces to WALKOFF in Kubernetes.
    """
    pass


command_groups = {
    cli: [install_command, uninstall_command, status, version],
    update: update_commands,
    local: local_commands,
    dev: dev_commands,
    deploy: deploy_commands
}


def add_commands():
    for command_group, commands in command_groups.items():
        for command in commands:
            command_group.add_command(command)
