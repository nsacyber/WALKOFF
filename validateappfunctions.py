import argparse
import os
from core.config.paths import apps_path
from core.helpers import list_apps, import_app_main, list_class_functions
import inspect
from apps import App as BaseApp
import yaml

base_app_functions = set(list_class_functions(BaseApp))


def cmd_line():
    parser = argparse.ArgumentParser(description="Validate functions.json for apps")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=False,
                        help='List of apps for which you would like to validate')
    args = parser.parse_args()
    return args


def get_app_main(app_name):
    try:
        app_main = getattr(import_app_main(app_name), 'Main')
        return app_main
    except AttributeError:
        print('In app {0}: Critical!: App has no class called Main!'.format(app_name))
        return None


def get_app_bases(app_name, app_main):
    bases = inspect.getmro(app_main)
    if BaseApp in bases:
        return bases
    else:
        print('In app {0}: Critical!: The Main class does not extend apps.App!'.format(app_name))
        return None


def list_all_app_functions(app_name):
    app_main = get_app_main(app_name)
    if app_main:
        app_bases = get_app_bases(app_name, app_main)
        if app_bases:
            app_functions = set(list_class_functions(app_main)) - base_app_functions
            if not app_functions:
                print('In app {0}: Error: App has no functions!'.format(app_name))
            else:
                return app_functions
    return None


def load_functions_yaml(app_name):
    filename = os.path.join(apps_path, app_name, 'api.yaml')
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as function_file:
                function_yaml = yaml.load(function_file)
                if not function_yaml:
                    print('In app {0}: Error: api.yaml has no actions!'.format(app_name))
                    return None
                else:
                    return function_yaml
        except (IOError, OSError) as e:
            print('Error reading {0}'.format(filename))
            print(e)
            return None
    else:
        print('In app {0}: Critical!: api.yaml does '
              'not exist in expected location {1}!'.format(app_name, filename))
        return None


def validate_functions_exist(app_name, app_functions, funcs_yaml):
    yaml_funcs = set()
    for action in funcs_yaml['actions'].values():
        yaml_funcs.add(action['run'])
    extra_funcs_in_app_class = app_functions - yaml_funcs
    for extra_func in extra_funcs_in_app_class:
        print('In app {0}: Warning: function {1} found in app which is not included in '
              'api.yaml'.format(app_name, extra_func))
    extra_funcs_in_yaml = yaml_funcs - app_functions
    for extra_func in extra_funcs_in_yaml:
        print('In app {0}: Warning: function {1} found in api.yaml which is in app'.format(app_name, extra_func))


# TODO: Delete this. It is no longer necessary with the switch from JSON to YAML...and it didn't do much to begin with
# def validate_fields(app_name, funcs_yaml):
#     for func, info in funcs_yaml['actions'].items():
#         print(func, info)
#         if 'params' not in info:
#             print('In app {0}: Critical! "args" field not found in functions.json for function {1}'.format(app_name,
#                                                                                                            func))
#         if 'description' not in info:
#             print('In app {0}: Warning: "description" field '
#                   'not found in functions.json for function {1}'.format(app_name, func))
#         elif not info['description']:
#             print('In app {0}: Warning: "description" field function {1} is empty'.format(app_name, func))


# TODO: Delete this. Again no longer necessary with the switch from JSON to YAML.
# def check_duplicate_aliases(app_name, funcs_json):
#     for func1, info1 in funcs_json.items():
#         for func2, info2 in funcs_json.items():
#             if func1 != func2 and 'aliases' in info1 and 'aliases' in info2:
#                 overlap = set(info1['aliases']) & set(info2['aliases'])
#                 if overlap:
#                     print('In app {0}: Error: Function {1} and function {2} '
#                           'have same aliases {3}!'.format(app_name, func1, func2, list(overlap)))


def validate_app(app_name):
    print('Validating App {0}'.format(app_name))
    app_functions = list_all_app_functions(app_name)
    function_yaml = load_functions_yaml(app_name)
    if app_functions and function_yaml:
        validate_functions_exist(app_name, app_functions, function_yaml)
        # validate_fields(app_name, function_yaml)
        # check_duplicate_aliases(app_name, function_yaml)


if __name__ == '__main__':
    cmd_args = cmd_line()
    all_apps = list_apps()
    if not cmd_args.apps:
        for app in all_apps:
            validate_app(app)
    else:
        for app in cmd_args.apps:
            if app in all_apps:
                validate_app(app)
            else:
                print('App {0} not found!'.format(app))
