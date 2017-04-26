import os
import sys
import importlib
import json
from flask import Blueprint, render_template, request, g, Response
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


@app_page.route('/actions', methods=['GET'])
@auth_token_required
@roles_required('admin')
def list_app_actions():
    core.config.config.load_function_info()
    if g.app in core.config.config.function_info['apps']:
        return json.dumps({'status': 'success',
                           'actions': core.config.config.function_info['apps'][g.app]})
    else:
        return json.dumps({'status': 'error: app name not found'})

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


# Controls the non-specific app device configuration
@app_page.route('/devices', methods=['GET'])
@auth_token_required
@roles_required('admin')
def list_devices():
    query = running_context.Device.query.all()
    output = []
    if query:
        for device in query:
            if g.app == device.app.name:
                output.append(device.as_json())
    return json.dumps(output)


@app_page.route('/devices/<string:device_name>', methods=['PUT'])
@auth_token_required
@roles_required('admin')
def add_device(device_name):
    form = forms.AddNewDeviceForm(request.form)
    if form.validate():
        if len(running_context.Device.query.filter_by(name=device_name).all()) > 0:
            return json.dumps({"status": "device could not be added"})

        running_context.Device.add_device(name=device_name, username=form.username.data,
                                          password=form.pw.data, ip=form.ipaddr.data, port=form.port.data,
                                          app_server=g.app,
                                          extra_fields=form.extraFields.data)
        return json.dumps({"status": "device successfully added"})
    return json.dumps({"status": "device could not be added"})


@app_page.route('/devices/<string:device_name>', methods=['GET'])
@auth_token_required
@roles_required('admin')
def display_device(device_name):
    dev = running_context.Device.query.filter_by(name=device_name).first()
    if dev is not None:
        return json.dumps(dev.as_json())
    return json.dumps({"status": "could not display device"})


@app_page.route('/devices/<string:device_name>', methods=['POST'])
@auth_token_required
@roles_required('admin')
def update_device(device_name):
    form = forms.EditDeviceForm(request.args)
    dev = running_context.Device.query.filter_by(name=device_name).first()
    if form.validate() and dev is not None:
        dev.edit_device(form)
        running_context.db.session.commit()
        return json.dumps({"status": "device successfully edited"})
    return json.dumps({"status": "device could not be edited"})


@app_page.route('/devices/<string:device_name>', methods=['DELETE'])
@auth_token_required
@roles_required('admin')
def delete_device(device_name):
    dev = running_context.Device.query.filter_by(name=device_name).first()
    if dev is not None:
        running_context.db.session.delete(dev)
        running_context.db.session.commit()
        return json.dumps({"status": "removed device"})
    return json.dumps({"status": "could not remove device"})


@app_page.route('/devices/import', methods=['GET'])
@auth_token_required
@roles_required('admin')
def import_devices():
    form = forms.ExportImportAppDevices(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_appdevice_export_path
    try:
        with open(filename, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            apps_devices = json.loads(read_file)
    except (OSError, IOError):
        return json.dumps({"status": "error reading file"})
    for app in apps_devices:
        for device in apps_devices[app]:
            extra_fields = {}
            for key in device:
                if key not in ['ip', 'name', 'port', 'username']:
                    extra_fields[key] = device[key]
            extra_fields_str = json.dumps(extra_fields)
            running_context.Device.add_device(name=device['name'], username=device['username'], ip=device['ip'],
                                              port=device['port'],
                                              extra_fields=extra_fields_str, app_server=app, password='')
    return json.dumps({"status": "success"})


@app_page.route('/devices/export', methods=['POST'])
@auth_token_required
@roles_required('admin')
def export_devices():
    form = forms.ExportImportAppDevices(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_appdevice_export_path
    returned_json = {}
    apps = running_context.App.query.all()
    for app in apps:
        devices = []
        for device in app.devices:
            device_json = device.as_json(with_apps=False)
            device_json.pop('app', None)
            device_json.pop('id', None)
            devices.append(device_json)
        returned_json[app.as_json()['name']] = devices

    try:
        with open(filename, 'w') as appdevice_file:
            appdevice_file.write(json.dumps(returned_json, indent=4, sort_keys=True))
    except (OSError, IOError):
        return json.dumps({"status": "error writing file"})
    return json.dumps({"status": "success"})


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
