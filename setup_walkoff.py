import subprocess
import sys
import redis
import click
import os


def write_redis_info(rh, rp):
    from walkoff.config import Config
    Config.load_config()
    Config.CACHE = {'type': 'redis', 'host': rh, 'port': rp}
    Config.write_values_to_file(keys=["CACHE"])


@click.command()
@click.option('--unattended', default=False)
def main(unattended):
    click.echo('\nChecking if pip is installed:')
    try:
        click.echo(subprocess.check_output([sys.executable, "-m", "pip", "--version"]))
    except subprocess.CalledProcessError:
        click.echo("\nPlease install pip first, before running this installer.")
        return

    click.echo('\nInstalling Python Dependencies...')
    subprocess.call([sys.executable, "-m", "pip", "install", "-U", "-r", "requirements.txt"])
    subprocess.call([sys.executable, "scripts/install_dependencies.py"])

    click.echo('\nGenerating Certificates...')
    subprocess.call([sys.executable, "scripts/generate_certificates.py"])

    retry = False if (os.environ.get("CACHE", None) or unattended) else True

    while retry:
        rh = click.prompt('\nEnter IP or hostname of Redis server (default: localhost)',
                          default="localhost", show_default=False)
        rp = click.prompt('\nEnter port of Redis server (default: 6379)',
                          default=6379, show_default=False, type=int)
        try:
            r = redis.Redis(rh, port=rp)
            r.ping()
            write_redis_info(rh, rp)
            retry = False
        except redis.ConnectionError:
            if not click.confirm("Couldn't ping Redis at {}:{}. Specify a different IP/port?".format(rh, rp)):
                click.echo("Ensure that you have Redis running before starting walkoff.py.")
                return

    click.echo('\nDone setting up WALKOFF. You can now start WALKOFF by running the walkoff.py script.')


if __name__ == '__main__':
    main()
