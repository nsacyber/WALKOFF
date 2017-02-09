from setuptools import setup
import os
import argparse

def cmd_line():
    parser = argparse.ArgumentParser("Install Dependencies")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=True, help='List of apps for which you would like to install dependencies')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = cmd_line()
    apps = args.apps

    for app in apps:
        print "Installing dependencies for " + app + " App..."
        deps = []
        path = os.path.abspath('apps/' + app + '/setup.py')
        if os.path.isfile(path) is False:
            print "No setup.py script found in "+app+" folder. Skipping..."
            continue
        os.system("python "+path+" install")
