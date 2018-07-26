import click


@click.command()
@click.pass_context
def install(ctx):
    """ Installs Walkoff in a kubernetes cluster.

    If installing on kubernetes, Walkoff will use Helm to install itself onto the kubernetes cluster
    """
    click.echo('Installing Walkoff into kubernetes')