import argparse
from os import walk
import os.path
import re


def _convert_2_camelcase(input_value):
    if input_value[0] != input_value[:1].upper():
        input_value = input_value[:1].upper() + input_value[1:]
    if '-' in input_value or '_' in input_value:
        input_splits = re.findall('[A-Za-z0-9]+', input_value)
        input_formatted = [input_split[:1].upper() + input_split[1:] for input_split in input_splits]
        input_value = ''.join(input_formatted)
    return input_value


def _separate_camelcase(input_value):
    out = re.findall('[A-Z][a-z]*', input_value)
    return ' '.join(out)


def make_template(app_name):
    main_dir = os.path.dirname(os.path.realpath(__file__))
    apps_dir = main_dir + '/apps'
    skeleton_app_dir = apps_dir + '/SkeletonApp'

    # Create new app directory if it doesn't exists
    app_name = _convert_2_camelcase(app_name)
    new_app_dir = apps_dir + '/' + app_name
    if not os.path.exists(new_app_dir):
        os.makedirs(new_app_dir)

    for (dirpath, dirnames, filenames) in walk(skeleton_app_dir):
        if '__pycache__' not in dirpath:
            for fn in filenames:
                if dirpath == skeleton_app_dir:
                    write_fp = new_app_dir + '/' + fn
                else:
                    sub_dir = dirpath.replace(skeleton_app_dir, new_app_dir)
                    if not os.path.exists(sub_dir):
                        os.makedirs(sub_dir)
                    write_fp = sub_dir + '/' + fn

                with open(dirpath + '/' + fn) as read_from_file:
                    with open(write_fp, 'w') as write_to_file:
                        for line in read_from_file:
                            if 'SkeletonApp' in line:
                                line = line.replace('SkeletonApp', app_name)
                            elif 'Skeleton App' in line:
                                line = line.replace('Skeleton App', _separate_camelcase(app_name))

                            write_to_file.write(line)

parser = argparse.ArgumentParser(description='Make the template for a new app.')
parser.add_argument("app_name", type=make_template, help='Make template for app with name given by app_name. '
                                                         'The new app is stored under the "apps" directory.')
args = parser.parse_args()