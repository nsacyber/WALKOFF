import json
import sys
import os
from six.moves import configparser
from six.moves import input
import tarfile
import zipfile

walkoff_ext = ""
walkoff_internal = os.path.abspath(__file__).rsplit(os.path.sep, 1)[0]


def set_config_path():
    global walkoff_ext

    ext_json = os.path.join(walkoff_internal, 'config', 'external_paths.json')
    with open(ext_json, "r") as f:
        o = json.load(f)
        sys.stdout.write("* Enter a path for walkoff_external: ")
        user_input = input()
        walkoff_ext = user_input

        try:
            os.makedirs(walkoff_ext)
            o["walkoff_external"] = walkoff_ext
        except OSError:
            if os.path.isdir(walkoff_ext):
                print("Specified directory exists, assuming this is OK.")
                o["walkoff_external"] = walkoff_ext
            else:
                print("Specified directory could not be created.")
                sys.exit(1)

    with open(ext_json, "w") as f:
        json.dump(o, f, sort_keys=True)

    arch_path = os.path.join(walkoff_internal, "walkoff_external")

    # if os.name == 'posix':
    arch_path += ".tar.gz"
    archf = tarfile.open(arch_path)

    # elif os.name == 'nt':
    #     arch_path += ".zip"
    #     archf = zipfile.ZipFile(arch_path)

    archf.extractall(walkoff_ext)

def set_alembic_paths():

    config = configparser.ConfigParser()
    alembic_ini = os.path.join(walkoff_internal, 'scripts', 'migrations', 'alembic.ini')
    with open(alembic_ini, "r") as f:
        config.readfp(f)

    urlprefix = "sqlite:///"
    config.set("walkoff", "sqlalchemy.url", urlprefix + walkoff_ext + os.sep + "walkoff.db")
    config.set("events", "sqlalchemy.url", urlprefix + walkoff_ext + os.sep + "events.db")
    config.set("device", "sqlalchemy.url", urlprefix + walkoff_ext + os.sep + "devices.db")

    with open(alembic_ini, "w") as f:
        config.write(f)


def set_logging_path():

    logging_json = os.path.join(walkoff_ext, 'walkoff_data', 'log', 'logging.json')
    log_log = os.path.join(walkoff_ext, 'walkoff_data', 'log', 'log.log')
    with open(logging_json, "r") as f:
        o = json.load(f)
        o["handlers"]["file_handler"]["filename"] = log_log

    with open(logging_json, "w") as f:
        json.dump(o, f, indent=2, sort_keys=True)


def main():
    set_config_path()
    set_alembic_paths()
    set_logging_path()


if __name__ == '__main__':
    main()
