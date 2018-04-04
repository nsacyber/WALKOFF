import json
import sys
import os
from six.moves import configparser
from six.moves import input
import tarfile
import zipfile

from walkoff.config import Config


def set_walkoff_external():
    default = os.path.join(os.getcwd(), "walkoff_external")
    sys.stdout.write(" * Enter a directory to install WALKOFF apps, interfaces, and data to (default: {}): "
                     .format(default))
    Config.WALKOFF_EXTERNAL_PATH = input()

    if Config.WALKOFF_EXTERNAL_PATH == '':
        Config.WALKOFF_EXTERNAL_PATH = default

    if not Config.WALKOFF_EXTERNAL_PATH.lower().endswith("walkoff_external"):
        os.path.join(Config.WALKOFF_EXTERNAL_PATH, "walkoff_external")

    if not os.path.isdir(Config.WALKOFF_EXTERNAL_PATH):
        try:
            print("Creating {}".format(Config.WALKOFF_EXTERNAL_PATH))
            os.makedirs(Config.WALKOFF_EXTERNAL_PATH)
        except OSError as e:
            print("Specified directory could not be created: {}".format(e))
            sys.exit(1)

    Config.write_values_to_file()

    arch_path = os.path.join(Config.WALKOFF_INTERNAL_PATH, "walkoff_external")

    if os.name == 'posix':
        arch_path += ".tar.gz"
        archf = tarfile.open(arch_path)

    elif os.name == 'nt':
        arch_path += ".zip"
        archf = zipfile.ZipFile(arch_path)

    archf.extractall(Config.WALKOFF_EXTERNAL_PATH)


def set_alembic_paths():

    config = configparser.ConfigParser()
    alembic_ini = os.path.join(Config.WALKOFF_INTERNAL_PATH, 'scripts', 'migrations', 'alembic.ini')
    with open(alembic_ini, "r") as f:
        config.readfp(f)

    config.set("walkoff", "sqlalchemy.url", "sqlite:///{}".format(Config.DB_PATH))
    config.set("events", "sqlalchemy.url", "sqlite:///{}".format(Config.CASE_DB_PATH))
    config.set("execution", "sqlalchemy.url", "sqlite:///{}".format(Config.EXECUTION_DB_PATH))

    with open(alembic_ini, "w") as f:
        config.write(f)


def set_logging_path():

    logging_json = Config.LOGGING_CONFIG_PATH
    log_log = os.path.join(Config.DATA_PATH, 'log', 'log.log')
    with open(logging_json, "r") as f:
        o = json.load(f)
        o["handlers"]["file_handler"]["filename"] = log_log

    with open(logging_json, "w") as f:
        json.dump(o, f, indent=2, sort_keys=True)


def main():
    set_walkoff_external()
    set_alembic_paths()
    set_logging_path()


if __name__ == '__main__':
    main()
