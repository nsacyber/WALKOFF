import argparse
import ctypes as cts
import os
import shutil
import subprocess
import sys
import time
from distutils.util import strtobool

import semver
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

    from walkoff import __version__ as version

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

    my_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for root, dirnames, filenames in os.walk(my_dir, topdown=False):
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                print("Removing: " + os.path.join(root, filename))
                os.remove(os.path.join(root, filename))
        for dirname in dirnames:
            if dirname == "__pycache__":
                print("Removing: " + os.path.join(root, dirname))
                os.removedirs(os.path.join(root, dirname))


def setup(flagged, inter):
    if not (flagged or (inter and prompt("Do you want to setup WALKOFF now?"))):
        return

    from walkoff import setup_walkoff
    setup_walkoff.main()


def migrate_apps(flagged, inter):
    if not (flagged or (inter and prompt("Do you want to migrate your app APIs?"))):
        return

    from walkoff.scripts.migrate_api import convert_apis
    convert_apis()


def alembic(flagged, inter):
    if not (flagged or (inter and prompt("Do you want alembic to migrate databases? (This will install alembic.)"))):
        return

    path = os.path.join('.', 'data', 'devices.db')
    if os.path.isfile(path):
        new_path = os.path.join('.', 'data', 'execution.db')
        os.rename(path, new_path)

    names = ["execution", "events", "walkoff"]
    for name in names:
        try:
            r = (subprocess.check_output(["alembic", "--name", name, "current"], stderr=subprocess.STDOUT,
                                         universal_newlines=True))
            if "(head)" in r:
                print("Already up to date, no alembic upgrade needed.")
            else:
                if name == "walkoff":
                    subprocess.check_output(["alembic", "--name", name, "stamp", "dd74ff55c643"],
                                            stderr=subprocess.STDOUT, universal_newlines=True)
                print(subprocess.check_output(["alembic", "--name", name, "upgrade", "head"],
                                              stderr=subprocess.STDOUT, universal_newlines=True))
        except subprocess.CalledProcessError:
            print("Alembic encountered an error.")
            print("Try manually running 'alembic --name {} upgrade head".format(name))
            print("You may already be on the latest revision.")
            continue
        except OSError:
            print("alembic not installed, installing alembic...and then you must re-run update script")
            import pip
            pip.main(["install", "alembic"])
            break


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
    alembic(args.everything or args.migratedatabase, args.interactive)


if __name__ == '__main__':
    main()
