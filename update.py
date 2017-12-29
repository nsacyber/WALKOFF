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
from walkoff import __version__ as version


def prompt(question):

    while True:
        sys.stdout.write("\n* " + question + " yes/no? ")
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            print("Please respond with 'yes' or 'no'.")


def archive(flagged, inter):

    if inter and not prompt("Do you want to make a backup of the current directory?"):
        return
    elif not flagged:
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

    if inter and not prompt("Do you want to git pull from the current branch?"):
        return
    elif not flagged:
        return

    print("Pulling from current branch: ")
    print(subprocess.check_output(["git", "branch"], stderr=subprocess.STDOUT))
    print(subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT))


def clean_pycache(flagged, inter):

    if inter and not prompt("Do you want to clear pycache files?"):
        return
    elif not flagged:
        return

    my_dir = os.path.dirname(os.path.abspath(__file__))

    for root, dirnames, filenames in os.walk(my_dir):
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                print("Removing: " + os.path.join(root, filename))
                os.remove(os.path.join(root, filename))


def setup(flagged, inter):

    if inter and not prompt("Do you want to setup WALKOFF now?"):
        return
    elif not flagged:
        return

    setup_walkoff.main()


def migrate_apps(flagged, inter):

    if inter and not prompt("Do you want to migrate your app APIs?"):
        return
    elif not flagged:
        return

    scripts.migrate_api.main()


def migrate_workflows(flagged, inter):

    if inter and not prompt("Do you want to migrate your workflows?"):
        return
    elif not flagged:
        return

    scripts.migrate_workflows.main()


def alembic(flagged, inter):

    if inter and not prompt("Do you want alembic to migrate databases? (This will install alembic.)"):
        return
    elif not flagged:
        return

    for i in range(0, 1):
        try:
            r = (subprocess.check_output(["alembic", "current"], stderr=subprocess.STDOUT))
            if "(head)" in r:
                print("Already up to date, no alembic upgrade needed.")
            else:
                print(subprocess.check_output(["alembic", "upgrade", "head"], stderr=subprocess.STDOUT))
            return

        except OSError:
            print("alembic not installed, installing alembic...")
            import pip
            pip.main(["install", "alembic"])

    print("Could not install alembic, are you root/administrator?")


def main():

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
                        help="Runs workflow migration script. Not reversible at this time.",
                        action="store_true")

    parser.add_argument("-md", "--migratedatabase",
                        help="Runs alembic database migration.",
                        action="store_true")

    if not len(sys.argv) > 1:
        parser.print_help()
        print("\nPlease specify at least one of the above arguments.")
        return

    args = parser.parse_args()

    if args.everything or args.setup or args.migratedatabase:
        if (os.name == 'posix' and os.geteuid() != 0) or (os.name == 'nt' and cts.windll.shell32.IsUserAnAdmin() != 0):
            if not prompt("Using --setup or --migratedatabase requires root/administrator. Try anyways?"):
                return

    archive(args.everything or args.archive, args.interactive)
    git(args.everything or args.pull, args.interactive)
    clean_pycache(args.everything or args.clean, args.interactive)
    setup(args.everything or args.setup, args.interactive)
    migrate_apps(args.everything or args.migrateapps, args.interactive)
    migrate_workflows(args.everything or args.migrateworkflows, args.interactive)
    alembic(args.everything or args.migratedatabase, args.interactive)


if __name__ == '__main__':
    main()
