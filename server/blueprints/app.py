import os
import sys
import importlib
import json
from flask import Blueprint, render_template, request, g, current_app
from flask_security import roles_required, auth_token_required, roles_accepted
from server import forms
from server.flaskserver import running_context
import core.config.config
import core.config.paths

app_page = Blueprint('appPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')


@app_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.app = values.pop('app', None)
    app_page.static_folder = os.path.abspath(os.path.join('apps', g.app, 'interface', 'static'))


@app_page.route('/', methods=['GET'])
@auth_token_required
@roles_required('admin')
def read_app():
    form = forms.RenderArgsForm(request.form)
    path = '{0}/interface/templates/{1}'.format(g.app, form.page.data)  # Do not use os.path.join
    args = load_app(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


#TODO: DELETE
@app_page.route('/display', methods=['POST'])
@auth_token_required
@roles_required('admin')
def display_app():
    form = forms.RenderArgsForm(request.form)
    path = '{0}/interface/templates/{1}'.format(g.app, form.page.data)  # Do not use os.path.join
    args = load_app(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


# @app_page.route('/devices/export', methods=['POST'])
# @auth_token_required
# @roles_required('admin')
# def export_devices():
#     form = forms.ExportImportAppDevices(request.form)
#     filename = form.filename.data if form.filename.data else core.config.paths.default_appdevice_export_path
#     returned_json = {}
#     apps = running_context.App.query.all()
#     for app in apps:
#         devices = []
#         for device in app.devices:
#             device_json = device.as_json(with_apps=False)
#             device_json.pop('app', None)
#             device_json.pop('id', None)
#             devices.append(device_json)
#         returned_json[app.as_json()['name']] = devices
#     try:
#         with open(filename, 'w') as appdevice_file:
#             appdevice_file.write(json.dumps(returned_json, indent=4, sort_keys=True))
#     except (OSError, IOError) as e:
#         current_app.logger.error('Error importing devices from {0}: {1}'.format(filename, e))
#         return json.dumps({"status": "error writing file"})
#     current_app.logger.debug('Exported devices to {0}'.format(filename))
#     return json.dumps({"status": "success"})


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
