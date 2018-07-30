import click
from walkoff.helpers import compose_api as _componse_api
from ..local.util import clean_pycache
import os
import subprocess
from .download import download


@click.command()
@click.pass_context
def clean(ctx):
    clean_pycache(ctx.obj['dir'], ctx.obj['verbose'])


@click.group()
@click.pass_context
def generate(ctx):
    pass


@generate.command()
@click.pass_context
def api(ctx):
    """Recomposes the OpenAPI specification

    This operation must be performed after modifying the OpenAPI and running an individual test.
    """
    click.echo('Generating api...')
    _componse_api(ctx.obj['config'])


@generate.command()
def docs():
    os.chdir(os.path.join('docs'))
    subprocess.call(['make', 'html'], shell=True)


generate.add_command(download)


@click.group(name='open')
def open_command():
    pass


@open_command.command()
def docs():
    index = os.path.join('.', 'docs', '_build', 'html', 'index.html')
    if os.path.isfile(index):
        index = os.path.abspath(index)
        click.launch(index)
    else:
        click.echo(
            'Could not find docs path. Have you generated the docs yet? '
            'If not try "python -m walkoff dev generate docs"')


commands = [clean, generate, open_command]