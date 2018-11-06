import click
from walkoff.helpers import list_apps, list_interfaces
import subprocess

import json
import os
from six.moves import configparser
import tarfile
import zipfile

from walkoff.config import Config
from walkoff.helpers import format_db_path

from .gencerts import generate_certificates


@click.group(invoke_without_command=True)
@click.pass_context
def install(ctx):
    """ Installs Walkoff locally.

    Walkoff will create a working directory which can be used to specify configuration parameters and into which you
    can add apps and interfaces.
    """
    if ctx.invoked_subcommand is None:
        click.echo('Installing Walkoff Locally')
        walkoff_internal = os.path.abspath(__file__).rsplit(os.path.sep, 1)[0]
        set_walkoff_external(ctx, walkoff_internal)
        set_alembic_paths(walkoff_internal)
        set_logging_path()
        generate_certificates(Config.KEYS_PATH, Config.ZMQ_PUBLIC_KEYS_PATH, Config.ZMQ_PRIVATE_KEYS_PATH)


@install.group()
@click.option('-a', '--all', is_flag=True, help='Install dependencies for all apps and interfaces')
@click.pass_context
def deps(ctx, all):
    if all:
        apps_path = ctx.obj['config'].APPS_PATH if 'config' in ctx.obj else Config.APPS_PATH
        interfaces_path = ctx.obj['config'].INTERFACES_PATH if 'config' in ctx.obj else Config.INTERFACES_PATH
        _install_all_apps_interfaces(apps_path, interfaces_path)


def _install_all_apps_interfaces(apps_path, interfaces_path):
    apps_ = list_apps(apps_path)
    interfaces_ = list_interfaces(interfaces_path)
    install_apps(apps_, apps_path)
    install_interfaces(interfaces_, interfaces_path)


@deps.command()
@click.option('-s', '--select', help='Specify a comma-separated list of apps')
@click.pass_context
def apps(ctx, select):
    apps_path = ctx.obj['config'].APPS_PATH if 'config' in ctx.obj else Config.APPS_PATH
    apps_ = list_apps(apps_path) if not select else select.split(',')
    install_apps(apps_, apps_path)


@deps.command()
@click.option('-s', '--select', help='Specify a comma-separated list of interfaces')
@click.pass_context
def interfaces(ctx, select):
    click.echo('Installing interfaces with {}'.format(select))
    interfaces_path = ctx.obj['config'].INTERFACES_PATH if 'config' in ctx.obj else Config.INTERFACES_PATH
    interfaces_ = list_interfaces(interfaces_path) if not select else select
    install_interfaces(interfaces_, interfaces_path)


def install_apps(apps_, apps_path):
    for app in apps_:
        print("Installing dependencies for " + app + " App...")
        path = os.path.abspath(os.path.join(apps_path, app, 'requirements.txt'))
        install_python_deps_from_pip(app, path)


def install_interfaces(interfaces_, interfaces_path):
    for interface in interfaces_:
        click.echo("Installing dependencies for " + interface + " Interface...")
        path = os.path.abspath(os.path.join(interfaces_path, interface, 'requirements.txt'))
        install_python_deps_from_pip(interface, path)


def install_python_deps_from_pip(name, path):
    if os.path.isfile(path) is False:
        click.echo("No requirements.txt file found in {} folder. Skipping...".format(name))
    else:
        subprocess.call(['pip', 'install', '-r', path])


def set_walkoff_external(ctx, walkoff_internal):
    default = os.getcwd()
    external_path = click.prompt(
        " * Enter a directory to install WALKOFF apps, interfaces, and data to (default: {}): ".format(default),
        default=os.getcwd())

    external_path = os.path.abspath(external_path)

    if not os.path.isdir(external_path):
        try:
            click.echo("     Creating {}".format(external_path))
            os.makedirs(external_path)
        except OSError as e:
            click.echo("Specified directory could not be created: {}".format(e))
            ctx.exit(1)

    arch_path = os.path.join(walkoff_internal, "walkoff_external")

    try:
        if os.name == 'posix':
            arch_path += ".tar.gz"
            archf = tarfile.open(arch_path)
        elif os.name == 'nt':
            arch_path += ".zip"
            archf = zipfile.ZipFile(arch_path)
        else:
            raise ValueError('Unsupported OS {}'.format(os.name))
    except IOError:
        click.echo(
            "WALKOFF installation file does not exist. Please make sure the file exists at {} and try again.".format(
                arch_path))
        ctx.exit(1)

    archf.extractall(external_path)

    Config.DATA_PATH = os.path.join(external_path, 'data')

    Config.API_PATH = os.path.join(Config.DATA_PATH, 'api.yaml')
    Config.APPS_PATH = os.path.join(external_path, 'apps')
    Config.CACHE_PATH = os.path.join(Config.DATA_PATH, 'cache')
    Config.CACHE = {"type": "disk", "directory": Config.CACHE_PATH, "shards": 8, "timeout": 0.01, "retry": True}
    Config.CASE_DB_PATH = os.path.join(Config.DATA_PATH, 'events.db')

    Config.TEMPLATES_PATH = os.path.join(walkoff_internal, 'templates')
    Config.CLIENT_PATH = os.path.join(walkoff_internal, 'client')
    Config.CONFIG_PATH = os.path.join(Config.DATA_PATH, 'walkoff.config')
    Config.DB_PATH = os.path.join(Config.DATA_PATH, 'walkoff.db')
    Config.DEFAULT_APPDEVICE_EXPORT_PATH = os.path.join(Config.DATA_PATH, 'appdevice.json')
    Config.DEFAULT_CASE_EXPORT_PATH = os.path.join(Config.DATA_PATH, 'cases.json')
    Config.EXECUTION_DB_PATH = os.path.join(Config.DATA_PATH, 'execution.db')
    Config.INTERFACES_PATH = os.path.join(external_path, 'interfaces')
    Config.LOGGING_CONFIG_PATH = os.path.join(Config.DATA_PATH, 'log', 'logging.json')

    Config.WALKOFF_SCHEMA_PATH = os.path.join(Config.DATA_PATH, 'walkoff_schema.json')
    Config.WORKFLOWS_PATH = os.path.join(Config.DATA_PATH, 'workflows')

    Config.KEYS_PATH = os.path.join(external_path, '.certificates')
    Config.CERTIFICATE_PATH = os.path.join(Config.KEYS_PATH, 'walkoff.crt')
    Config.PRIVATE_KEY_PATH = os.path.join(Config.KEYS_PATH, 'walkoff.key')
    Config.ZMQ_PRIVATE_KEYS_PATH = os.path.join(Config.KEYS_PATH, 'private_keys')
    Config.ZMQ_PUBLIC_KEYS_PATH = os.path.join(Config.KEYS_PATH, 'public_keys')

    Config.write_values_to_file()

    return external_path


def set_alembic_paths(walkoff_internal):
    Config.load_config()
    config = configparser.ConfigParser()
    alembic_ini = os.path.join(walkoff_internal, 'scripts', 'migrations', 'alembic.ini')
    with open(alembic_ini, "r") as f:
        config.readfp(f)

    config.set("walkoff", "sqlalchemy.url", format_db_path(Config.WALKOFF_DB_TYPE, Config.DB_PATH))
    config.set("execution", "sqlalchemy.url", format_db_path(Config.EXECUTION_DB_TYPE, Config.EXECUTION_DB_PATH))

    with open(alembic_ini, "w") as f:
        config.write(f)


def set_logging_path():
    Config.load_config()
    logging_json = Config.LOGGING_CONFIG_PATH
    log_log = os.path.join(Config.DATA_PATH, 'log', 'log.log')
    with open(logging_json, "r") as f:
        o = json.load(f)
        o["handlers"]["file_handler"]["filename"] = log_log
        o["handlers"]["file_handler_with_proc"]["filename"] = log_log

    with open(logging_json, "w") as f:
        json.dump(o, f, indent=2, sort_keys=True)
