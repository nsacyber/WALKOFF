import os
import ctypes as cts
import sys
from distutils.util import strtobool
import subprocess
import shutil
import time
import argparse
import setup_walkoff
import scripts.migrate_api
import scripts.migrate_workflows
import semver
from walkoff import __version__ as version
from six.moves import input


def prompt(question):

    while True:
        sys.stdout.write("\n* " + question + " yes/no? ")
        try:
            s = input()
            return strtobool(s.lower())
        except ValueError:
            print("Please respond with 'yes' or 'no'.")


def archive(flagged, inter):

    if not (flagged or (inter and prompt("Do you want to make a backup of the current directory?"))):
        return

    if not os.path.exists("backups"):
        os.makedirs("backups")

    filename = "backups/" + version + "-" + time.strftime("%Y%m%d-%H%M%S")
    ext = ""

    if os.name == "nt":
        ext = "zip"
    elif os.name == "posix":
        ext = "gztar"

    print("Creating " + ext + " archive... (This might take a while)")
    shutil.make_archive(filename, ext)
    print("Backup created at " + filename)


def git(flagged, inter):

    if not (flagged or (inter and prompt("Do you want to git pull from the current branch?"))):
        return

    print("Pulling from current branch: ")
    print(subprocess.check_output(["git", "branch"], stderr=subprocess.STDOUT, universal_newlines=True))
    print(subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT, universal_newlines=True))


def clean_pycache(flagged, inter):

    if not (flagged or (inter and prompt("Do you want to clear pycache files?"))):
        return

    my_dir = os.path.dirname(os.path.abspath(__file__))

    for root, dirnames, filenames in os.walk(my_dir):
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                print("Removing: " + os.path.join(root, filename))
                os.remove(os.path.join(root, filename))


def setup(flagged, inter):

    if not (flagged or (inter and prompt("Do you want to setup WALKOFF now?"))):
        return

    setup_walkoff.main()


def migrate_apps(flagged, inter):

    if not (flagged or (inter and prompt("Do you want to migrate your app APIs?"))):
        return

    scripts.migrate_api.main()


def validate_version(target):
    if target is None:
        return None, None

    if target.startswith("d"):
        mode = "downgrade"
    elif target.startswith("u"):
        mode = "upgrade"
    else:
        print("Use 'd' or 'u' at the start to specify whether to downgrade or upgrade to the specified version.")
        return None, None

    tgt_version = target[1:]
    try:
        semver.parse(tgt_version)
    except ValueError:
        print("{} is not a valid semver string".format(tgt_version))
        return None, None

    return mode, tgt_version


def migrate_workflows(flagged, inter, target):

    if not (flagged or (inter and prompt("Do you want to migrate your workflows?"))):
        return

    mode, tgt_version = validate_version(target)
    while inter and (mode is None):
        target = input(
            "Enter the version target, e.g. 'u0.5.2' to upgrade to 0.5.2 or 'd0.5.0' to downgrade to 0.5.0: ")
        mode, tgt_version = validate_version(target)

    print("{} workflows to version {}".format(mode, tgt_version))
    scripts.migrate_workflows.convert_playbooks(mode, tgt_version)


def alembic(flagged, inter):

    if not (flagged or (inter and prompt("Do you want alembic to migrate databases? (This will install alembic.)"))):
        return

    for i in range(0, 1):
        try:
            # names = ["device", "events", "walkoff"]
            names = ["walkoff"]
            for name in names:
                try:
                    r = (subprocess.check_output(["alembic", "--name", name, "current"], stderr=subprocess.STDOUT,
                                                 universal_newlines=True))
                    if "(head)" in r:
                        print("Already up to date, no alembic upgrade needed.")
                    else:
                        print(subprocess.check_output(["alembic", "--name", name, "upgrade", "head"],
                                                      stderr=subprocess.STDOUT, universal_newlines=True))
                except subprocess.CalledProcessError as e:
                    print("Alembic encountered an error.")
                    print("Try manually running 'alembic --name {} upgrade head".format(name))
                    print("You may already be on the latest revision.")

                return
        except OSError:
            print("alembic not installed, installing alembic...")
            import pip
            pip.main(["install", "alembic"])

    print("Could not install alembic, are you root/administrator?")


def create_cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interactive",
                        help="Interactively prompt 'yes or no' for each choice.",
                        action="store_true")
    parser.add_argument("-e", "--everything",
                        help="Equivalent to using all flags",
                        action="store_true")
    parser.add_argument("-a", "--archive",
                        help="Creates a backup archive of the entire WALKOFF directory in backups/",
                        action="store_true")
    parser.add_argument("-p", "--pull",
                        help="Performs a 'git pull' from the currently set branch",
                        action="store_true")
    parser.add_argument("-c", "--clean",
                        help="Removes all .pyc and .pyo cache files.",
                        action="store_true")
    parser.add_argument("-s", "--setup",
                        help="Performs WALKOFF setup. Requires root/administrator privileges.",
                        action="store_true")
    parser.add_argument("-ma", "--migrateapps",
                        help="Runs app API migration script. Not reversible at this time.",
                        action="store_true")
    parser.add_argument("-mw", "--migrateworkflows",
                        help="Runs workflow migration script to upgrade/downgrade to the specified version,"
                             " e.g. 'u0.5.2' to upgrade to 0.5.2 or 'd0.5.0' to downgrade to 0.5.0")
    parser.add_argument("-md", "--migratedatabase",
                        help="Runs alembic database migration.",
                        action="store_true")
    return parser


def main():

    parser = create_cli_parser()

    if not len(sys.argv) > 1:
        parser.print_help()
        print("\nPlease specify at least one of the above arguments.")
        return

    args = parser.parse_args()

    if args.everything or args.setup or args.migratedatabase or args.interactive:
        if (os.name == 'posix' and os.geteuid() != 0) or (os.name == 'nt' and cts.windll.shell32.IsUserAnAdmin() != 0):
            if not prompt("Using --setup or --migratedatabase requires root/administrator. Try anyways?"):
                return

    archive(args.everything or args.archive, args.interactive)
    git(args.everything or args.pull, args.interactive)
    clean_pycache(args.everything or args.clean, args.interactive)
    setup(args.everything or args.setup, args.interactive)
    migrate_apps(args.everything or args.migrateapps, args.interactive)
    migrate_workflows(args.everything or args.migrateworkflows, args.interactive, args.migrateworkflows)
    alembic(args.everything or args.migratedatabase, args.interactive)


if __name__ == '__main__':
    main()
