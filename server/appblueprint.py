import os
import sys
import importlib
import json
from flask import Blueprint, render_template, request, g, Response
from flask_security import roles_required, auth_token_required
from . import forms
import core.config.config
import core.config.paths
from core.helpers import construct_module_name_from_path

appPage = Blueprint('appPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')


@appPage.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.app = values.pop('app', None)
    appPage.static_folder = os.path.abspath(os.path.join(core.config.paths.apps_path, g.app, 'interface', 'static'))


@appPage.route('/display', methods=['POST'])
@auth_token_required
@roles_required('admin')
def display_app():
    form = forms.RenderArgsForm(request.form)
    path = os.path.join(g.app, 'interface', 'templates', form.page.data)
    args = load_app(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


@appPage.route('/stream/<string:stream_name>')
@roles_required('admin')
def stream_app_data(stream_name):
    stream_generator, stream_type = data_stream(g.app, stream_name)
    if stream_generator and stream_type:
        return Response(stream_generator(), mimetype=stream_type)


def load_module(app_name):
    app_path = os.path.join(core.config.paths.apps_path, app_name, 'display.py')
    module_name = construct_module_name_from_path(app_path[:-3])
    try:
        return sys.modules[module_name]
    except KeyError:
        pass
    try:
        return importlib.import_module(module_name, '')
    except ImportError:
        return None


def load_app(name, keys, values):
    module = load_module(name)
    args = dict(zip(keys, values))
    return getattr(module, "load")(args) if module else {}


def data_stream(app_name, stream_name):
    module = load_module(app_name)
    if module:
        return getattr(module, 'stream_generator')(stream_name)


@appPage.route('/actions', methods=['GET'])
@auth_token_required
@roles_required('admin')
def list_app_actions():
    core.config.config.load_function_info()
    if g.app in core.config.config.function_info['apps']:
        return json.dumps({'status': 'success',
                           'actions': core.config.config.function_info['apps'][g.app]})
    else:
        return json.dumps({'status': 'error: app name not found'})
