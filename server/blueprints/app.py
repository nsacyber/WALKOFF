import os
import sys
import importlib
from flask import Blueprint, render_template, request, g
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from server import forms

app_page = Blueprint('appPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')


@app_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.app = values.pop('app', None)
    app_page.static_folder = os.path.abspath(os.path.join('apps', g.app, 'interface', 'static'))


@app_page.route('/', methods=['GET'])
@jwt_required
@roles_accepted('admin')
def read_app():
    form = forms.RenderArgsForm(request.form)
    path = '{0}/interface/templates/{1}'.format(g.app, form.page.data)  # Do not use os.path.join
    args = load_app(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


# TODO: DELETE
@app_page.route('/display', methods=['POST'])
@jwt_required
@roles_accepted('admin')
def display_app():
    form = forms.RenderArgsForm(request.form)
    path = '{0}/interface/templates/{1}'.format(g.app, form.page.data)  # Do not use os.path.join
    args = load_app(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


def load_module(app_name):
    module_name = 'apps.{0}.display'.format(app_name)
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
    return getattr(module, 'load')(args) if module else {}


def data_stream(app_name, stream_name):
    module = load_module(app_name)
    if module:
        return getattr(module, 'stream_generator')(stream_name)
