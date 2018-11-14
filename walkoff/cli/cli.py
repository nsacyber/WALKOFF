import click
import os

from .update import commands as update_commands
from .install import install as install_command
from .install import uninstall as uninstall_command
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
@click.option('-c', '--config', help='The configuration file of the Walkoff installation')
@click.pass_context
def local(ctx, dir, config):
    """Controls local installations of Walkoff
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
    """Functions useful for developing Walkoff
    """
    import walkoff.config
    load_config(os.getcwd())
    ctx.obj['config'] = walkoff.config.Config
    ctx.obj['dir'] = os.getcwd()


@cli.group()
@click.pass_context
def deploy(ctx):
    """Deploy apps and interfaces.
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
