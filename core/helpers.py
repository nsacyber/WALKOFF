import importlib
import sys
import json
import os

from core.config import workflowsPath


def returnCytoscapeData(steps):
    output = []
    for step in steps:
        node = {"group": "nodes", "data": {"id": steps[step]["name"]}}
        output.append(node)
        for next in steps[step].conditionals:
            edgeId = str(steps[step]["name"]) + str(next["name"])
            if next["name"] in steps:
                node = {"group": "edges", "data": {"id": edgeId, "source": steps[step]["name"], "target": next["name"]}}
            output.append(node)
    return output

def import_lib(dir, module_name):
    module = None
    try:
        module = importlib.import_module('.'.join(['core', dir, module_name]))
    except ImportError:
        pass
    finally:
        return module


def import_app_main(app_name):
    module = "apps." + app_name + ".main"
    try:
        return sys.modules[module]
    except KeyError:
        pass
    try:
        return importlib.import_module(module, 'Main')
    except ImportError:
        pass


def list_apps(path=os.path.join('.', 'apps')):
    return [f for f in os.listdir(path) if (os.path.isdir(os.path.join('.', 'apps', f))
                                            and not f.startswith('__'))]


def load_function_aliases(app_name):
    alias_file = os.path.join('.', 'apps', app_name, 'functionAliases.json')
    if os.path.isfile(alias_file):
        with open(alias_file, 'r') as aliases:
            return json.loads(aliases.read())


def list_class_functions(class_name):
    return [field for field in dir(class_name) if (not field.startswith('_')
                                                   and callable(getattr(class_name, field)))]


def list_app_functions(app_name):
    app_module = importlib.import_module('apps.' + app_name + '.main')
    if app_module:
        try:
            main_class = getattr(app_module, 'Main')
            return list_class_functions(main_class)
        except AttributeError:
            return []
    return []


def load_app_function(app_instance, function_name):
    try:
        fn = getattr(app_instance, function_name)
        return fn
    except AttributeError:
        return None


def locate_workflows_in_directory(path=workflowsPath):
    return [workflow for workflow in os.listdir(path) if (os.path.isfile(os.path.join(path, workflow))
                                                          and workflow.endswith('.workflow'))]
