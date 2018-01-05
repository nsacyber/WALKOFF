import argparse
import os.path
import re
from os import walk

import yaml

main_dir = os.path.dirname(os.path.realpath(__file__))
apps_dir = main_dir + '/apps'


def _convert_2_camelcase(input_value):
    if input_value[0] != input_value[:1].upper():
        input_value = input_value[:1].upper() + input_value[1:]
    if '-' in input_value or '_' in input_value or ' ' in input_value:
        input_splits = re.findall('[A-Za-z0-9]+', input_value)
        input_formatted = [input_split[:1].upper() + input_split[1:] for input_split in input_splits]
        input_value = ''.join(input_formatted)
    return input_value


def _separate_camelcase(input_value):
    out = re.findall('[A-Z][a-z0-9]*', input_value)
    return ' '.join(out)


def make_template(app_name):
    skeleton_app_dir = apps_dir + '/SkeletonApp'

    # Create new app directory if it doesn't exists
    app_name = _convert_2_camelcase(app_name)
    new_app_dir = apps_dir + '/' + app_name
    if not os.path.exists(new_app_dir):
        os.makedirs(new_app_dir)
        for (dirpath, dirnames, filenames) in walk(skeleton_app_dir):
            if '__pycache__' not in dirpath:
                for filename in filenames:
                    write_fp = get_write_filepath(dirpath, filename, new_app_dir, skeleton_app_dir)
                    write_app_to_file(app_name, dirpath, filename, write_fp)
        print('Finished generating the template at', new_app_dir)
    else:
        print('Template already exist at', new_app_dir)


def write_app_to_file(app_name, dirpath, filename, write_fp):
    with open(dirpath + '/' + filename) as read_from_file:
        with open(write_fp, 'w') as write_to_file:
            for line in read_from_file:
                if 'SkeletonApp' in line:
                    line = line.replace('SkeletonApp', app_name)
                elif 'Skeleton App' in line:
                    line = line.replace('Skeleton App', _separate_camelcase(app_name))
                write_to_file.write(line)


def get_write_filepath(dirpath, filename, new_app_dir, skeleton_app_dir):
    if dirpath == skeleton_app_dir:
        write_fp = new_app_dir + '/' + filename
    else:
        sub_dir = dirpath.replace(skeleton_app_dir, new_app_dir)
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)
        write_fp = sub_dir + '/' + filename
    return write_fp


def generate_methods(input_fp):
    actual_fp = get_actual_filepath(input_fp)
    if actual_fp == '':
        print('Unable to find file. Please check that the yaml file exist at', input_fp)
        return

    with open(actual_fp) as yaml_file:
        yaml_dict = yaml.load(yaml_file)

    app_name = _convert_2_camelcase(yaml_dict['info']['title'])
    new_app_dir = apps_dir + '/' + app_name
    if not os.path.exists(new_app_dir):
        print('Unable to find directory. Please check that the app exist at', new_app_dir)
        return

    main_py = new_app_dir + '/main.py'
    init_lines = []
    with open(main_py) as read_from_file:
        for line in read_from_file:
            if '@action' in line:
                break
            else:
                init_lines.append(line)
    with open(main_py, 'w') as write_to_file:
        write_to_file.writelines(init_lines[:max(loc for loc, val in enumerate(init_lines) if val == '\n') + 1])
    with open(main_py, 'a') as write_to_file:
        actions = yaml_dict['actions']
        for action, action_val in actions.items():
            write_action(action, action_val, write_to_file)
    cur_fp = new_app_dir + '/api.yaml'
    if actual_fp != cur_fp:
        with open(actual_fp) as yaml_file:
            with open(cur_fp, 'w') as write_to_file:
                for line in yaml_file:
                    write_to_file.write(line)
        print('Updated', cur_fp)
    print('Successfully generated methods for {0} at {1}'.format(_separate_camelcase(app_name), new_app_dir))


def get_actual_filepath(input_fp):
    actual_fp = ''
    if input_fp.count('/') > 0:
        if os.path.isfile(input_fp):
            actual_fp = input_fp
    else:
        for (dirpath, dirnames, filenames) in walk(main_dir):
            if input_fp in filenames:
                actual_fp = dirpath + '/' + input_fp
    return actual_fp


def write_action(action, action_val, write_to_file):
    lines = []
    if 'description' in action_val:
        lines.append("'''")
        lines.append(action_val['description'])
    parameters_args = ''
    if 'parameters' in action_val:
        parameters_args = add_parameters(action_val, lines)
    if 'returns' in action_val:
        add_returns(action_val, lines)
    lines.append('@action')
    lines.append('def {0}(self{1}):'.format(action.replace(' ', '_'), parameters_args))
    lines.append('\tpass')
    lines.append('\n')
    write_to_file.writelines('\n'.join(['\t' + line for line in lines]))


def add_returns(action_val, lines):
    success_val = action_val['returns']['Success']
    lines.append('Output:')
    lines.append('{0}: {1}'.format(success_val['schema']['type'], success_val['description']))
    lines.append("'''")


def add_parameters(action_val, lines):
    parameters0 = action_val['parameters'][0]
    lines.append('Inputs:')
    parameters_str = '{0} ({1}): {2}'.format(parameters0['name'], parameters0['type'],
                                             parameters0['description'])
    parameters_args = ', ' + parameters0['name']
    required_val = parameters0['required']
    if not required_val:
        parameters_str += ' (Optional)'
        parameters_args += '=None'
    lines.append(parameters_str)
    return parameters_args


help_msg_app_name = 'make template for app with name provided by app_name. The new app is stored under the "apps" ' \
                    'directory.'
help_msg_yaml = 'generate methods for app using yaml file at the filepath provided. If YAML_FILE is a filename, ' \
                'then it is assumed the file is located inside the WALKOFF directory; otherwise, an absolute ' \
                'filepath is required. If there are multiple files with the same filename, then the first file ' \
                'found will be used.'

parser = argparse.ArgumentParser(description='Make the template for a new app.')
parser.add_argument("--app_name", type=make_template, help=help_msg_app_name)
parser.add_argument("--yaml", type=generate_methods, help=help_msg_yaml, metavar=('YAML_FILE'))
args = parser.parse_args()
