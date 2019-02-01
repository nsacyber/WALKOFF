import argparse
import os
import sys

sys.path.append(os.path.abspath('.'))

import subprocess

from walkoff.helpers import list_apps, list_interfaces


def cmd_line():
    parser = argparse.ArgumentParser("Install Dependencies")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=False,
                        help='List of apps for which you would like to install dependencies')
    parser.add_argument('-i', '--interfaces', nargs='*', type=str, required=False,
                        help='List of interfaces for which you would like to install dependencies')
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = cmd_line()
    apps = args.apps
    interfaces = args.interfaces
    from walkoff.config import Config

    if not apps:
        apps = list_apps(Config.APPS_PATH)

    if not interfaces:
        interfaces = list_interfaces(Config.INTERFACES_PATH)

    for app in apps:
        print("Installing dependencies for " + app + " App...")
        path = os.path.abspath(os.path.join('apps', app, 'requirements.txt'))
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in " + app + " folder. Skipping...")
            continue
        subprocess.call([sys.executable, "-m", "pip", "install", "-U", "-r", path])

    for interface in interfaces:
        print("Installing dependencies for " + interface + " Interface...")
        path = os.path.abspath(os.path.join('interfaces', interface, 'requirements.txt'))
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in " + interface + " folder. Skipping...")
            continue
        subprocess.call([sys.executable, "-m", "pip", "install", "-U", "-r", path])
