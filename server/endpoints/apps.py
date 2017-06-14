import json
from flask import current_app, request
from flask_security import roles_accepted, auth_token_required
import core.config.config
import core.config.paths
from core import helpers
from server.return_codes import *
from server import forms
import pyaes


def read_all_apps():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return {"apps": helpers.list_apps()}, SUCCESS

    return __func()


def __format_app_action_api(api):
    ret = {}
    data_in = api.get('dataIn', False)
    if 'description' in api:
        ret['description'] = api['description']
    args = []
    if 'parameters' in api:
        for arg in api['parameters']:
            if data_in and arg['name'] == data_in:
                continue
            arg = dict(arg)
            arg.pop('name')
            args.append(arg)
    ret['args'] = args
    return ret


def __format_all_app_actions(app_api):
    return {action_name: __format_app_action_api(action_api)
            for action_name, action_api in app_api['actions'].items()}


def read_all_app_actions():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return {app_name: __format_all_app_actions(app_api)
                for app_name, app_api in core.config.config.app_apis.items()},  SUCCESS

    return __func()


def list_app_actions(app_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        try:
            app_api = core.config.config.app_apis[app_name]
        except KeyError:
            current_app.logger.error('Could not get action for app {0}. App does not exist'.format(app_name))
            return {'error': 'App name not found.'}, OBJECT_DNE_ERROR
        else:
            return {'actions': __format_all_app_actions(app_api)}, SUCCESS

    return __func()


def read_all_devices(app_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        if app_name in core.config.config.app_apis.keys():
            query = running_context.Device.query.all()
            output = []
            if query:
                for device in query:
                    if app_name == device.app.name:
                        output.append(device.as_json())
            return output, SUCCESS
        else:
            current_app.logger.error('Could not get devices for app {0}. App does not exist'.format(app_name))
            return {'error': 'App name not found.'}, OBJECT_DNE_ERROR

    return __func()


def create_device(app_name, device_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        form = forms.AddNewDeviceForm(request.form)
        if app_name in core.config.config.app_apis.keys():
            if len(running_context.Device.query.filter_by(name=device_name).all()) > 0:
                current_app.logger.error('Could not create device {0} for app {1}. '
                                         'Device already exists.'.format(device_name, app_name))
                return {"error": "Device already exists."}, OBJECT_EXISTS_ERROR

            try:
                with open(core.config.paths.AES_key_path, 'rb') as key_file:
                    key = key_file.read()
            except (OSError, IOError) as e:
                current_app.logger.error('Could not create device {0} for app {1}. '
                                         'Could not get key from AES key file'.format(device_name, app_name))
                return {"error": "Could not read key from AES key file."}, INVALID_INPUT_ERROR
            else:
                aes = pyaes.AESModeOfOperationCTR(key)
                pw = form.pw.data
                enc_pw = aes.encrypt(pw)

            running_context.Device.add_device(name=device_name, username=form.username.data,
                                              password=enc_pw, ip=form.ipaddr.data, port=form.port.data,
                                              app_server=app_name, extra_fields=form.extraFields.data)
            return {}, OBJECT_CREATED
        else:
            current_app.logger.error('Could not create device {0} for app {1}. '
                                     'App does not exist'.format(device_name, app_name))
            return {"error": "App does not exist."}, OBJECT_DNE_ERROR

    return __func()


def read_device(app_name, device_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        if app_name in core.config.config.app_apis.keys():
            dev = running_context.Device.query.filter_by(name=device_name).first()
            if dev is not None:
                return dev.as_json(), SUCCESS
            else:
                current_app.logger.error('Could not read device {0} for app {1}. '
                                         'Device does not exist'.format(device_name, app_name))
                return {"error": "Device does not exist."}, OBJECT_DNE_ERROR
        else:
            current_app.logger.error('Could not read device {0} for app {1}. '
                                     'App does not exist'.format(device_name, app_name))
            return {"error": "App does not exist."}, OBJECT_DNE_ERROR

    return __func()


def update_device(app_name, device_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        form = forms.EditDeviceForm(request.form)
        if app_name in core.config.config.app_apis.keys():
            dev = running_context.Device.query.filter_by(name=device_name).first()
            if dev is not None:
                dev.edit_device(form)
                running_context.db.session.commit()
                current_app.logger.info('Editing device {0}:{1} to {2}'.format(dev.app_id,
                                                                               dev.name,
                                                                               dev.as_json(with_apps=False)))

                return {}, SUCCESS
            else:
                current_app.logger.error('Could not update device {0} for app {1}. '
                                         'Device does not exist'.format(device_name, app_name))
                return {"error": "Device does not exist"}, OBJECT_DNE_ERROR
        else:
            current_app.logger.error('Could not update device {0} for app {1}. '
                                     'App does not exist'.format(device_name, app_name))
            return {"error": "App does not exist"}, OBJECT_DNE_ERROR

    return __func()


def delete_device(app_name, device_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        if app_name in core.config.config.app_apis.keys():
            dev = running_context.Device.query.filter_by(name=device_name).first()
            if dev is not None:
                running_context.db.session.delete(dev)
                current_app.logger.info('Device removed {0}:{1}'.format(app_name, device_name))
                running_context.db.session.commit()
                return {}, SUCCESS
            else:
                current_app.logger.error('Could not delete device {0} for app {1}. '
                                         'Device does not exist'.format(device_name, app_name))
                return {"error": "Device does not exist"}, OBJECT_DNE_ERROR
        else:
            current_app.logger.error('Could not delete device {0} for app {1}. '
                                     'App does not exist'.format(device_name, app_name))
            return {"error": "App does not exist"}, OBJECT_DNE_ERROR

    return __func()


def import_devices(app_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        form = forms.ExportImportAppDevices(request.form)
        filename = form.filename.data if form.filename.data else core.config.paths.default_appdevice_export_path
        try:
            with open(filename, 'r') as appdevice_file:
                read_file = appdevice_file.read()
                read_file = read_file.replace('\n', '')
                apps_devices = json.loads(read_file)
        except (OSError, IOError) as e:
            current_app.logger.error('Error importing devices from {0}: {1}'.format(filename, e))
            return {"error": "Error reading file."}, IO_ERROR
        for app in apps_devices:
            for device in apps_devices[app]:
                extra_fields = {}
                for key in device:
                    if key not in ['ip', 'name', 'port', 'username']:
                        extra_fields[key] = device[key]
                extra_fields_str = json.dumps(extra_fields)
                running_context.Device.add_device(name=device['name'], username=device['username'], ip=device['ip'],
                                                  port=device['port'],
                                                  extra_fields=extra_fields_str, app_server=app, password=None)
        current_app.logger.debug('Imported devices from {0}'.format(filename))
        return {}, SUCCESS

    return __func()


def export_devices(app_name):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
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
        except (OSError, IOError) as e:
            current_app.logger.error('Error importing devices from {0}: {1}'.format(filename, e))
            return {"error": "Error writing file"}, IO_ERROR
        else:
            current_app.logger.debug('Exported devices to {0}'.format(filename))
            return {}, SUCCESS

    return __func()
