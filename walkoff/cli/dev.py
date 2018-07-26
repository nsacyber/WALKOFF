import click
from walkoff.helpers import compose_api as _componse_api
from .local.util import clean_pycache


@click.command(name='compose-api')
@click.pass_context
def compose_api(ctx):
    """Recomposes the OpenAPI specification

    This operation must be performed after modifying the OpenAPI and running an individual test.
    """
    click.echo('composing api...')
    _componse_api(ctx.obj['config'])


@click.command()
@click.pass_context
def clean(ctx):
    clean_pycache(ctx.obj['dir'], ctx.obj['verbose'])


commands = [compose_api, clean]