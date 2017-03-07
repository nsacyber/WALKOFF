import importlib
import sys
import json
from os import path

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


def load_function_aliases(app_name):
    alias_file = path.join('.', 'apps', app_name, 'functionAliases.json')
    if path.isfile(alias_file):
        with open(alias_file, 'r') as aliases:
            return json.loads(aliases.read())


def load_app_function(app_instance, function_name):
    try:
        fn = getattr(app_instance, function_name)
        return fn
    except AttributeError:
        return None
