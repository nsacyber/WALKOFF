import argparse
import os
import sys

sys.path.append(os.path.abspath('.'))

import pip

from walkoff.helpers import list_apps, list_interfaces


def cmd_line():
    parser = argparse.ArgumentParser("Install Dependencies")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=False,
                        help='List of apps for which you would like to install dependencies')
    parser.add_argument('-i', '--interfaces', nargs='*', type=str, required=False,
                        help='List of interfaces for which you would like to install dependencies')
    args = parser.parse_args()
    return args


def install_dependencies():
    args = cmd_line()
    apps = args.apps
    interfaces = args.interfaces

    if not apps:
        apps = list_apps()

    if not interfaces:
        interfaces = list_interfaces()

    for app in apps:
        print("Installing dependencies for " + app + " App...")
        path = os.path.abspath('apps/' + app + '/requirements.txt')
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in " + app + " folder. Skipping...")
            continue
        pip.main(['install', '-r', path])

    for interface in interfaces:
        print("Installing dependencies for " + interface + " Interface...")
        path = os.path.abspath('interfaces/' + interface + '/requirements.txt')
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in " + interface + " folder. Skipping...")
            continue
        pip.main(['install', '-r', path])


if __name__ == '__main__':
    install_dependencies()
