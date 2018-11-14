import click


@click.command()
@click.pass_context
def apps(ctx):
    """
    WIP - Update WALKOFF apps inside Kubernetes cluster

    Gets the current set of apps from a GitHub repository and restarts the workers and server to use the updated apps.

    Note: All currently executing workflows will be paused and all pending workflows will be aborted during this
    operation.
    """
    click.echo('updating apps {} on kubernetes'.format(ctx.obj['local']))


@click.command()
@click.pass_context
def interfaces(ctx):
    """
    WIP - Update WALKOFF interfaces inside Kubernetes cluster

    Gets the current set of interfaces from a GitHub repository and restarts the server to use the updated interfaces.

    Note: All currently executing workflows will be paused and all pending workflows will be aborted during this
    operation.
    """
    click.echo('updating interfaces {} on kubernetes'.format(ctx.obj['local']))


commands = [apps, interfaces]
