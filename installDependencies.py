import argparse
import pip
import os

def cmd_line():

    parser = argparse.ArgumentParser("Command Line Parser")

    parser.add_argument('-a', '--app', type=str, required=True, nargs='*', help='Specify name of app(s) to install dependencies')

    args = parser.parse_args()

    return args

def install(package):
    pip.main(['install', package])

if __name__ == '__main__':

    args = cmd_line()

    for app in args.app:
        print "Installing dependencies for "+app+" App..."

        file = os.path.abspath('apps/'+app+'/dependencies.txt')
        with open(file) as f:
            for dependency in f:
                install(dependency)
