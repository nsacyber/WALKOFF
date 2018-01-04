import json

from flask import current_app, request
from flask_jwt_extended import jwt_required

import walkoff.config.paths
from walkoff.devicedb import Device, App, device_db
from walkoff.helpers import get_app_device_api, InvalidArgument, UnknownDevice, UnknownApp, format_exception_message
from walkoff.appgateway.validator import validate_device_fields
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions


def get_device_json_with_app_name(device):
    device_json = device.as_json()
    app = device_db.session.query(App).filter(App.id == device.app_id).first()
    device_json['app_name'] = app.name if app is not None else ''
    return device_json


def read_all_devices():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['read']))
    def __func():
        return [get_device_json_with_app_name(device) for device in device_db.session.query(Device).all()], SUCCESS

    return __func()


def read_device(device_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['read']))
    def __func():
        device = device_db.session.query(Device).filter(Device.id == device_id).first()
        if device is not None:
            return get_device_json_with_app_name(device), SUCCESS

        else:
            current_app.logger.error('Could not read device {0}. '
                                     'Device does not exist'.format(device_id))
            return {"error": "Device does not exist."}, OBJECT_DNE_ERROR

    return __func()


def delete_device(device_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['delete']))
    def __func():
        dev = device_db.session.query(Device).filter(Device.id == device_id).first()
        if dev is not None:
            device_db.session.delete(dev)
            current_app.logger.info('Device removed {0}'.format(device_id))
            device_db.session.commit()
            return {}, SUCCESS
        else:
            current_app.logger.error('Could not delete device {0}. '
                                     'Device does not exist'.format(device_id))
            return {"error": "Device does not exist"}, OBJECT_DNE_ERROR

    return __func()


def add_configuration_keys_to_device_json(device_fields, device_fields_api):
    device_fields_api = {field['name']: field for field in device_fields_api}
    for field in device_fields:
        add_configuration_keys_to_field(device_fields_api, field)


def add_configuration_keys_to_field(device_fields_api, field):
    if field['name'] in device_fields_api:
        field['type'] = device_fields_api[field['name']]['type']
        if 'encrypted' in device_fields_api[field['name']]:
            field['encrypted'] = device_fields_api[field['name']]['encrypted']


def create_device():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['create']))
    def __func():
        add_device_json = request.get_json()
        if device_db.session.query(Device).filter(Device.name == add_device_json['name']).first() is not None:
            current_app.logger.error('Could not create device {0}. '
                                     'Device already exists.'.format(add_device_json['name']))
            return {"error": "Device already exists."}, OBJECT_EXISTS_ERROR

        fields = {field['name']: field['value'] for field in add_device_json['fields']}
        app = add_device_json['app_name']
        device_type = add_device_json['type']
        try:
            device_api = get_app_device_api(app, device_type)
            device_fields_api = device_api['fields']
            validate_device_fields(device_fields_api, fields, device_type, app)
        except (UnknownApp, UnknownDevice, InvalidArgument) as e:
            return __crud_device_error_handler('create', e, app, device_type)
        else:
            fields = add_device_json['fields']
            add_configuration_keys_to_device_json(fields, device_fields_api)
            app = device_db.session.query(App).filter(App.name == app).first()
            if app is None:
                current_app.logger.error('SEVERE: App defined in api does not have corresponding entry in database. '
                                         'Cannot add device')
                return {'error': 'Unknown app'}, INVALID_INPUT_ERROR
            device = Device.from_json(add_device_json)
            app.add_device(device)
            device_db.session.add(device)
            device_db.session.commit()
            device_json = get_device_json_with_app_name(device)
            # remove_configuration_keys_from_device_json(device_json)
            return device_json, OBJECT_CREATED

    return __func()


def update_device():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['update']))
    def __func():
        update_device_json = request.get_json()
        device = device_db.session.query(Device).filter(Device.id == update_device_json['id']).first()
        if device is None:
            current_app.logger.error('Could not update device {0}. '
                                     'Device does not exist.'.format(update_device_json['id']))
            return {"error": "Device does not exist."}, OBJECT_DNE_ERROR

        fields = ({field['name']: field['value'] for field in update_device_json['fields']}
                  if 'fields' in update_device_json else None)
        app = update_device_json['app_name']
        device_type = update_device_json['type'] if 'type' in update_device_json else device.type
        try:
            device_api = get_app_device_api(app, device_type)
            device_fields_api = device_api['fields']
            if fields is not None:
                validate_device_fields(device_fields_api, fields, device_type, app)
        except (UnknownApp, UnknownDevice, InvalidArgument) as e:
            return __crud_device_error_handler('update', e, app, device_type)
        else:
            if fields is not None:
                fields = update_device_json['fields'] if 'fields' in update_device_json else None
                add_configuration_keys_to_device_json(fields, device_fields_api)
            device.update_from_json(update_device_json)
            device_db.session.commit()
            device_json = get_device_json_with_app_name(device)
            # remove_configuration_keys_from_device_json(device_json)
            return device_json, SUCCESS

    return __func()


__device_error_messages = {UnknownApp: ('App does not exist', 'Unknown app'),
                           UnknownDevice: ('Type does not exist', 'Unknown device type'),
                           InvalidArgument: ('Invalid input', 'Invalid device fields')}


def __crud_device_error_handler(operation, exception, app, device_type):
    ret = __device_error_messages[exception.__class__]
    current_app.logger.error(
        'Could not {0} device for app {1}, type {2}. {3}'.format(operation, app, device_type, ret[0]))
    return {'error': ret[1]}, INVALID_INPUT_ERROR


def import_devices():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['create']))
    def __func():
        data = request.get_json()
        filename = data['filename'] if 'filename' in data else walkoff.config.paths.default_appdevice_export_path
        try:
            with open(filename, 'r') as devices_file:
                read_file = devices_file.read()
                read_file = read_file.replace('\n', '')
                apps = json.loads(read_file)
        except (OSError, IOError) as e:
            current_app.logger.error('Error importing devices from {0}: {1}'.format(filename, e))
            return {"error": "Error reading file."}, IO_ERROR
        for app in apps:
            for device in apps[app]:
                if device_db.session.query(Device).filter(Device.name == device['name']).first() is not None:
                    current_app.logger.error('Could not import device {0}. '
                                             'Device already exists.'.format(device['name']))
                    continue
                fields = {field['name']: field['value'] for field in device['fields']}
                device_type = device['type']
                app = import_device(app, device, device_type, fields)

        current_app.logger.debug('Imported devices from {0}'.format(filename))
        return {}, SUCCESS

    return __func()


def import_device(app, device, device_type, fields):
    try:
        device_api = get_app_device_api(app, device_type)
        device_fields_api = device_api['fields']
        validate_device_fields(device_fields_api, fields, device_type, app)
    except UnknownDevice:
        current_app.logger.error('Cannot import device for app {0}, type {1}. '
                                 'Type does not exist'.format(app, device_type))
    except InvalidArgument as e:
        current_app.logger.error('Cannot import device for app {0}, type {1}. '
                                 'Invalid input'.format(app, device_type,
                                                        format_exception_message(e)))
    else:
        fields = device['fields']
        add_configuration_keys_to_device_json(fields, device_fields_api)
        app = device_db.session.query(App).filter(App.name == app).first()
        if app is not None:
            device_obj = Device.from_json(device)
            app.add_device(device_obj)
            device_db.session.add(device_obj)
            device_db.session.commit()
        else:
            current_app.logger.error(
                'SEVERE: App defined in api does not have corresponding entry in database. '
                'Cannot import device')
    return app


def export_devices():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('devices', ['read']))
    def __func():
        data = request.get_json()
        filename = data['filename'] if 'filename' in data else walkoff.config.paths.default_appdevice_export_path
        returned_json = get_exported_json()
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


def get_exported_json():
    returned_json = {}
    apps = device_db.session.query(App).all()
    for app in apps:
        devices = []
        for device in app.devices:
            device_json = device.as_json(export=True)
            device_json.pop('app', None)
            device_json.pop('id', None)
            devices.append(device_json)
        returned_json[app.as_json()['name']] = devices
    return returned_json