import argparse
import os
import sys

sys.path.append(os.path.abspath('.'))

import pip

from walkoff.helpers import list_apps


def cmd_line():
    parser = argparse.ArgumentParser("Install Dependencies")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=False,
                        help='List of apps for which you would like to install dependencies')
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = cmd_line()
    apps = args.apps

    if not apps:
        apps = list_apps()

    for app in apps:
        print("Installing dependencies for " + app + " App...")
        path = os.path.abspath('apps/' + app + '/requirements.txt')
        if os.path.isfile(path) is False:
            print("No requirements.txt file found in " + app + " folder. Skipping...")
            continue
        pip.main(['install', '-r', path])
