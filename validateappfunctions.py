import argparse
import json
import os
from core.config.paths import apps_path
from core.helpers import list_apps, import_app_main, list_class_functions
import inspect
from server.appdevice import App as BaseApp

base_app_functions = set(list_class_functions(BaseApp))

def cmd_line():
    parser = argparse.ArgumentParser(description="Validate functions.json for apps")
    parser.add_argument('-a', '--apps', nargs='*', type=str, required=False,
                        help='List of apps for which you would like to validate')
    parser.add_argument('-A', '--all', action='store_true', help='Validate all apps')
    args = parser.parse_args()
    return args


def get_app_main(app_name):
    try:
        app = getattr(import_app_main(app_name), 'Main')
        return app
    except AttributeError:
        print('In app {0}: Critical!: App has no class called Main!'.format(app_name))
        return None


def get_app_bases(app_name, app_main):
    bases = inspect.getmro(app_main)
    if BaseApp in bases:
        return bases
    else:
        print('In app {0}: Critical!: The Main class does not extend server.appDevice.App!'.format(app_name))
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


def load_functions_json(app_name):
    filename = os.path.join(apps_path, app_name, 'functions.json')
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as function_file:
                function_json = json.loads(function_file.read())
                if not function_json:
                    print('In app {0}: Error: functions.json has no actions!'.format(app_name))
                    return None
                else:
                    return function_json
        except (IOError, OSError) as e:
            print('Error reading {0}'.format(filename))
            print(e)
            return None
    else:
        print('In app {0}: Critical!: functions.json does not exist in expected location {1}!'.format(app_name,
                                                                                                     filename))
        return None


def validate_functions_exist(app_name, app_functions, funcs_json):
    json_funcs = set(list(funcs_json.keys()))
    extra_funcs_in_app_class = app_functions - json_funcs
    for extra_func in extra_funcs_in_app_class:
        print('In app {0}: Warning: function {1} found in app which is not included in '
              'functions.json'.format(app_name, extra_func))
    extra_funcs_in_json = json_funcs - app_functions
    for extra_func in extra_funcs_in_json:
        print('In app {0}: Warning: function {1} found in functions.json which is in app'.format(app_name, extra_func))


def validate_fields(app_name, funcs_json):
    for func, info in funcs_json.items():
        if 'args' not in info:
            print('In app {0}: Critical! "args" field not found in functions.json for function {1}'.format(app_name,
                                                                                                           func))
        if 'description' not in info:
            print('In app {0}: Warning: "description" field not found in functions.json for function {1}'.format(app_name, func))
        elif not info['description']:
            print('In app {0}: Warning: "description" field function {1} is empty'.format(app_name, func))


def check_duplicate_aliases(app_name, funcs_json):
    for func1, info1 in funcs_json.items():
        for func2, info2 in funcs_json.items():
            if func1 != func2 and 'aliases' in info1 and 'aliases' in info2:
                overlap = set(info1['aliases']) & set(info2['aliases'])
                if overlap:
                    print('In app {0}: Error: Function {1} and function {2} '
                          'have same aliases {3}!'.format(app_name, func1, func2, list(overlap)))


def validate_app(app_name):
    print('Validating App {0}'.format(app_name))
    app_functions = list_all_app_functions(app_name)
    function_json = load_functions_json(app_name)
    if app_functions and function_json:
        validate_functions_exist(app_name, app_functions, function_json)
        validate_fields(app_name, function_json)
        check_duplicate_aliases(app_name, function_json)


if __name__ == '__main__':
    cmd_args = cmd_line()
    all_apps = list_apps()
    if cmd_args.all:
        for app in all_apps:
            validate_app(app)
    else:
        for app in cmd_args.apps:
            if app in all_apps:
                validate_app(app)
            else:
                print('App {0} not found!'.format(app))





