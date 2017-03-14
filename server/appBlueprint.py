import os
import sys
import importlib
import json
from flask import Blueprint, render_template, request, g, Response
from flask_security import roles_required, auth_token_required
from . import forms
from core.helpers import list_app_functions, list_class_functions, load_function_aliases, list_apps

appPage = Blueprint('appPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')

base_app_functions = None


def get_base_app_functions():
    global base_app_functions
    if not base_app_functions:
        from server.appDevice import App as BaseApp
        base_app_functions = set(list_class_functions(BaseApp))
    return base_app_functions


@appPage.url_value_preprocessor
def staticRequestHandler(endpoint, values):
    g.app = values.pop('app', None)
    appPage.static_folder = os.path.abspath('apps/' + g.app + '/interface/static')


@appPage.route('/display', methods=['POST'])
@auth_token_required
@roles_required('admin')
def displayApp():
    form = forms.RenderArgsForm(request.form)
    path = g.app + '/interface/templates/' + form.page.data
    args = loadApp(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


@appPage.route('/stream/<string:stream_name>')
@roles_required('admin')
def stream_app_data(stream_name):
    stream_generator, stream_type = data_stream(g.app, stream_name)
    if stream_generator and stream_type:
        return Response(stream_generator(), mimetype=stream_type)


def loadModule(name):
    module = "apps." + name + ".display"
    try:
        return sys.modules[module]
    except KeyError:
        pass
    try:
        return importlib.import_module(module, '')
    except ImportError:
        return None


def loadApp(name, keys, values):
    module = loadModule(name)
    args = dict(zip(keys, values))
    return getattr(module, "load")(args) if module else {}


def data_stream(app_name, stream_name):
    module = loadModule(app_name)
    if module:
        return getattr(module, 'stream_generator')(stream_name)


@appPage.route('/actions', methods=['GET'])
@auth_token_required
@roles_required('admin')
def list_app_actions():
    get_base_app_functions()
    functions = set(list_app_functions(g.app)) - base_app_functions
    return json.dumps({"actions": list(functions)})


@appPage.route('/actions/aliases', methods=['GET'])
@auth_token_required
@roles_required('admin')
def list_app_function_aliases():
    return json.dumps(load_function_aliases(g.app))



