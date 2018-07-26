import json

import click
import requests

from .run import run
from .install import install
from .update import update


@click.command()
@click.pass_context
@click.option(
    '-H',
    '--host',
    help='The host address of a running Walkoff server. Defaults to setting contained in ./data/walkoff.config'
)
@click.option(
    '-p',
    '--port',
    help='The port to of a running Walkoff server. Defaults to setting contained in ./data/walkoff.config',
    type=int
)
def status(ctx, host, port):
    """Gets the status/health of Walkoff.

    Note: this command is a proxy for
    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://host:port/health
    """
    if not (host or port):
        host = ctx.obj['config'].HOST
        port = ctx.obj['config'].PORT
    click.echo('Getting status from {}:{}'.format(host, port))
    try:
        response = requests.get('http://{}:{}/health'.format(host, port))
    except Exception:
        click.echo('Could not connect to Walkoff instance at {}:{}'.format(host, port))
        ctx.exit(1)
    data = response.json()
    click.echo(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))


@click.command(name='gen-certs')
@click.pass_context
def generate_certificates(ctx):
    """Generates certificates
    """
    click.echo('generating certificates')


commands = [install, status, run, generate_certificates]