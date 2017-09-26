import json
from flask import current_app, request
from server.security import roles_accepted_for_resources
from flask_jwt_extended import jwt_required
import core.config.config
import core.config.paths
from server.returncodes import *
from core.validator import validate_device_fields
from core.helpers import get_app_device_api, InvalidInput, UnknownDevice, UnknownApp, format_exception_message
from server.database import db


def get_device_json_with_app_name(device):
    from server.context import running_context
    device_json = device.as_json()
    app = running_context.App.query.filter_by(id=device.app_id).first()
    device_json['app'] = app.name if app is not None else ''
    return device_json


def read_all_devices():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        return [get_device_json_with_app_name(device) for device in running_context.Device.query.all()], SUCCESS

    return __func()


def read_device(device_id):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        device = running_context.Device.query.filter_by(id=device_id).first()
        if device is not None:
            return get_device_json_with_app_name(device), SUCCESS
        else:
            current_app.logger.error('Could not read device {0}. '
                                     'Device does not exist'.format(device_id))
            return {"error": "Device does not exist."}, OBJECT_DNE_ERROR

    return __func()


def delete_device(device_id):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        dev = running_context.Device.query.filter_by(id=device_id).first()
        if dev is not None:
            db.session.delete(dev)
            current_app.logger.info('Device removed {0}'.format(device_id))
            db.session.commit()
            return {}, SUCCESS
        else:
            current_app.logger.error('Could not delete device {0}. '
                                     'Device does not exist'.format(device_id))
            return {"error": "Device does not exist"}, OBJECT_DNE_ERROR

    return __func()


def add_configuration_keys_to_device_json(device_fields, device_fields_api):
    device_fields_api = {field['name']: field for field in device_fields_api}
    for field in device_fields:
        if field['name'] in device_fields_api:
            field['type'] = device_fields_api[field['name']]['type']
            if 'encrypted' in device_fields_api:
                field['encrypted'] = device_fields_api['name']['encrypted']


# TODO: Delete. No longer used.
# def remove_configuration_keys_from_device_json(device_json):
#     for field in device_json['fields']:
#         field.pop('type')
#         if 'encrypted' in field:
#             field.pop('encrypted')


def create_device():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        add_device_json = request.get_json()
        if running_context.Device.query.filter_by(name=add_device_json['name']).first() is not None:
            current_app.logger.error('Could not create device {0}. '
                                     'Device already exists.'.format(add_device_json['name']))
            return {"error": "Device already exists."}, OBJECT_EXISTS_ERROR

        fields = {field['name']: field['value'] for field in add_device_json['fields']}
        app = add_device_json['app']
        device_type = add_device_json['type']
        try:
            device_api = get_app_device_api(app, device_type)
            device_fields_api = device_api['fields']
            validate_device_fields(device_fields_api, fields, device_type, app)
        except UnknownApp:
            current_app.logger.error('Cannot create device for app {0}, type {1}. '
                                     'App does not exist'.format(app, device_type))
            return {'error': 'Unknown app'}, INVALID_INPUT_ERROR
        except UnknownDevice:
            current_app.logger.error('Cannot create device for app {0}, type {1}. '
                                     'Type does not exist'.format(app, device_type))
            return {'error': 'Unknown device type'}, INVALID_INPUT_ERROR
        except InvalidInput as e:
            current_app.logger.error('Cannot create device for app {0}, type {1}. '
                                     'Invalid input'.format(app, device_type,
                                                            format_exception_message(e)))
            return {'error': 'Invalid device fields'}, INVALID_INPUT_ERROR
        else:
            fields = add_device_json['fields']
            add_configuration_keys_to_device_json(fields, device_fields_api)
            app = running_context.App.query.filter_by(name=app).first()
            if app is None:
                current_app.logger.error('SEVERE: App defined in api does not have corresponding entry in database. '
                                         'Cannot add device')
                return {'error': 'Unknown app'}, INVALID_INPUT_ERROR
            device = running_context.Device.from_json(add_device_json)
            app.add_device(device)
            db.session.add(device)
            db.session.commit()
            device_json = get_device_json_with_app_name(device)
            # remove_configuration_keys_from_device_json(device_json)
            return device_json, OBJECT_CREATED

    return __func()


def update_device():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        update_device_json = request.get_json()
        device = running_context.Device.query.filter_by(id=update_device_json['id']).first()
        if device is None:
            current_app.logger.error('Could not update device {0}. '
                                     'Device does not exist.'.format(update_device_json['id']))
            return {"error": "Device does not exist."}, OBJECT_DNE_ERROR

        fields = ({field['name']: field['value'] for field in update_device_json['fields']}
                  if 'fields' in update_device_json else None)
        app = update_device_json['app']
        device_type = update_device_json['type'] if 'type' in update_device_json else device.type
        try:
            device_api = get_app_device_api(app, device_type)
            device_fields_api = device_api['fields']
            if fields is not None:
                validate_device_fields(device_fields_api, fields, device_type, app)
        except UnknownApp:
            current_app.logger.error('Cannot update device for app {0}, type {1}. '
                                     'App does not exist'.format(app, device_type))
            return {'error': 'Unknown app'}, INVALID_INPUT_ERROR
        except UnknownDevice:
            current_app.logger.error('Cannot update device for app {0}, type {1}. '
                                     'Type does not exist'.format(app, device_type))
            return {'error': 'Unknown device type'}, INVALID_INPUT_ERROR
        except InvalidInput as e:
            current_app.logger.error('Cannot update device for app {0}, type {1}. '
                                     'Invalid input'.format(app, device_type,
                                                            format_exception_message(e)))
            return {'error': 'Invalid device fields'}, INVALID_INPUT_ERROR
        else:
            if fields is not None:
                fields = update_device_json['fields'] if 'fields' in update_device_json else None
                add_configuration_keys_to_device_json(fields, device_fields_api)
            device.update_from_json(update_device_json)
            db.session.commit()
            device_json = get_device_json_with_app_name(device)
            # remove_configuration_keys_from_device_json(device_json)
            return device_json, SUCCESS

    return __func()


def import_devices():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        data = request.get_json()
        filename = data['filename'] if 'filename' in data else core.config.paths.default_appdevice_export_path
        try:
            with open(filename, 'r') as devices_file:
                read_file = devices_file.read()
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
                                                  port=device['port'], extra_fields=extra_fields_str, password=None,
                                                  app_id=app)
        current_app.logger.debug('Imported devices from {0}'.format(filename))
        return {}, SUCCESS

    return __func()


def export_devices():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        data = request.get_json()
        filename = data['filename'] if 'filename' in data else core.config.paths.default_appdevice_export_path
        returned_json = {}
        apps = running_context.App.query.all()
        for app in apps:
            devices = []
            for device in app.devices:
                device_json = device.as_json()
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
