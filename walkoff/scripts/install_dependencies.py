import argparse
import os
import sys

sys.path.append(os.path.abspath('.'))

import subprocess

from walkoff.helpers import list_valid_directories
from walkoff import config


def cmd_line():
    parser = argparse.ArgumentParser("Install Dependencies")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=False,
                        help='List of apps for which you would like to install dependencies')
    parser.add_argument('-i', '--interfaces', nargs='*', type=str, required=False,
                        help='List of interfaces for which you would like to install dependencies')
    args = parser.parse_args()
    return args


def install_dependencies(apps=None, interfaces=None):

    if not apps:
        apps = list_valid_directories(config.Config.APPS_PATH)

    if not interfaces:
        interfaces = list_valid_directories(config.Config.INTERFACES_PATH)

    for app in apps:
        print("Installing dependencies for " + app + " App...")
        path = os.path.abspath(os.path.join(config.Config.APPS_PATH, app, 'requirements.txt'))
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in {}. Skipping...".format(path))
            continue
        subprocess.call(['pip', 'install', '-r', path])

    for interface in interfaces:
        print("Installing dependencies for " + interface + " Interface...")
        path = os.path.abspath(os.path.join(config.Config.INTERFACES_PATH, interface, 'requirements.txt'))
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in {}. Skipping...".format(path))
            continue
        subprocess.call(['pip', 'install', '-r', path])


def main():
    args = cmd_line()
    install_dependencies(args.apps, args.interfaces)


if __name__ == '__main__':
    main()