import json
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context, current_user, write_playbook_to_file
from server import forms
import core.config.config
import core.config.paths


configurations_page = Blueprint('settings_page', __name__)


@configurations_page.route('/<string:key>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def config_values(key):
    if current_user.is_authenticated and key:
        if hasattr(core.config.paths, key):
            return json.dumps({str(key): str(getattr(core.config.paths, key))})
        elif hasattr(core.config.config, key):
            return json.dumps({str(key): str(getattr(core.config.config, key))})
        else:
            return json.dumps({str(key): "Error: key not found"})
    else:
        return json.dumps({str(key): "Error: user is not authenticated or key is empty"})


@configurations_page.route('/set', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def set_configuration():
    if current_user.is_authenticated:
        form = forms.SettingsForm(request.form)
        if form.validate():
            for key, value in form.data.items():
                if hasattr(core.config.paths, key):
                    if key == 'workflows_path' and key != core.config.paths.workflows_path:
                        for playbook in running_context.controller.get_all_playbooks():
                            try:
                                write_playbook_to_file(playbook)
                            except (IOError, OSError):
                                pass
                        core.config.paths.workflows_path = value
                        running_context.controller.workflows = {}
                        running_context.controller.load_all_workflows_from_directory()
                    else:
                        setattr(core.config.paths, key, value)
                        if key == 'apps_path':
                            core.config.config.load_function_info()
                else:
                    setattr(core.config.config, key, value)
            return json.dumps({"status": 'success'})
        else:
            return json.dumps({"status": 'error: invalid form'})
    else:
        return json.dumps({"status": 'error: user is not authenticated'})


# Controls the non-specific app device configuration
@configurations_page.route('/<string:app>/devices', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def list_devices(app):
    query = running_context.Device.query.all()
    output = []
    if query:
        for device in query:
            if app == device.app.name:
                output.append(device.as_json())
    return json.dumps(output)


# Controls the non-specific app device configuration
@configurations_page.route('/<string:app>/devices/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def config_devices_config(app, action):
    if action == 'add':
        form = forms.AddNewDeviceForm(request.form)
        if form.validate():
            if len(running_context.Device.query.filter_by(name=form.name.data).all()) > 0:
                return json.dumps({"status": "device could not be added"})

            running_context.Device.add_device(name=form.name.data, username=form.username.data,
                                              password=form.pw.data, ip=form.ipaddr.data, port=form.port.data,
                                              app_server=app,
                                              extra_fields=form.extraFields.data)
            return json.dumps({"status": "device successfully added"})
        return json.dumps({"status": "device could not be added"})
    elif action == 'all':
        query = running_context.App.query.filter_by(name=app).first()
        output = []
        if query:
            for device in query.devices:
                output.append(device.as_json())

            return json.dumps(output)
        return json.dumps({"status": "could not display all devices"})
    elif action == 'export':
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

    elif action == 'import':
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


# Controls the specific app device configuration
@configurations_page.route('/<string:app>/devices/<string:device>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def config_devices_config_id(app, device, action):
    if action == 'remove':
        dev = running_context.Device.query.filter_by(name=device).first()
        if dev is not None:
            running_context.db.session.delete(dev)
            running_context.db.session.commit()
            return json.dumps({"status": "removed device"})
        return json.dumps({"status": "could not remove device"})


# Controls the specific app device edit configuration
@configurations_page.route('/<string:app>/devices/<string:device>/<string:action>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def config_devices_config_id_edit(app, device, action):
    if action == 'display':
        dev = running_context.Device.query.filter_by(name=device).first()
        if dev is not None:
            return json.dumps(dev.as_json())
        return json.dumps({"status": "could not display device"})
    if action == 'edit':
        form = forms.EditDeviceForm(request.args)
        dev = running_context.Device.query.filter_by(name=device).first()
        if form.validate() and dev is not None:
            dev.edit_device(form)
            running_context.db.session.commit()
            return json.dumps({"status": "device successfully edited"})
        return json.dumps({"status": "device could not be edited"})
