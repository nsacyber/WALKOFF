import os
import sys
from distutils.util import strtobool
import subprocess
import shutil
import time
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


def archive():
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


def git():
    print("Pulling from current branch: ")
    print(subprocess.check_output(["git", "branch"], stderr=subprocess.STDOUT))
    print(subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT))


def clean_pycache():
    my_dir = os.path.dirname(os.path.abspath(__file__))

    for root, dirnames, filenames in os.walk(my_dir):
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                print("Removing: " + os.path.join(root, filename))
                os.remove(os.path.join(root, filename))


def alembic():
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
    if prompt("Do you want to make a backup of the current directory?"):
        archive()
    if prompt("Do you want to git pull from the current branch?"):
        git()
    if prompt("Do you want to clear pycache files?"):
        clean_pycache()
    if prompt("Do you want to setup WALKOFF now?"):
        setup_walkoff.main()
    if prompt("Do you want to migrate your app apis?"):
        scripts.migrate_api.main()
    if prompt("Do you want to migrate your workflows?"):
        scripts.migrate_workflows.main()
    if prompt("Do you wish to use alembic to migrate databases? (This will install alembic if you don't have it.)"):
        alembic()


if __name__ == '__main__':
    main()
