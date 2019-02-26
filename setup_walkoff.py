import subprocess
import sys
import os
import argparse


def write_redis_info(rh, rp):
    from walkoff.config import Config
    Config.load_config()
    Config.CACHE = {'type': 'redis', 'host': rh, 'port': rp}
    Config.write_values_to_file(keys=["CACHE"])
    print('\nWrote Redis cache info to {}'.format(Config.CONFIG_PATH))


def install_deps():
    print('\nChecking if pip is installed:')
    try:
        print(subprocess.check_output([sys.executable, "-m", "pip", "--version"]).decode())
    except subprocess.CalledProcessError:
        print("\nPlease install pip first, before running this installer.")
        return

    print('\nInstalling Python Dependencies...')
    subprocess.call([sys.executable, "-m", "pip", "install", "-U", "-r", "requirements.txt"])
    subprocess.call([sys.executable, "scripts/install_dependencies.py"])


def gen_zmq_certs():
    print('\nGenerating Certificates...')
    subprocess.call([sys.executable, "scripts/generate_certificates.py"])


def check_redis(unattended):
    import click
    import redis
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--unattended", action='store_true', default=False)
    args = ap.parse_args()

    install_deps()
    gen_zmq_certs()
    check_redis(args.unattended)
