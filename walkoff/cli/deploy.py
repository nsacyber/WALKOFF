import click


@click.command()
@click.pass_context
@click.option('-p', '--path', help='Path to compressed app')
@click.option('-r', '--repo', help='Path to the git repository for the apps')
def app(ctx, path, repo):
    """Deploys a new app to Walkoff
    """
    pass


@click.command()
@click.pass_context
@click.option('-p', '--path', help='Path to compressed app')
@click.option('-r', '--repo', help='Path to the git repository for the interfaces')
def interface(ctx, path, repo):
    """Deploys a new interface to Walkoff
    """
    pass


commands = [app, interface]