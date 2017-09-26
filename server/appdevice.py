from sqlalchemy.ext.declarative import declared_attr
import pyaes
import logging
from server.database import db, TrackModificationsMixIn
from sqlalchemy.ext.hybrid import hybrid_property
from core.validator import convert_primitive_type
from server.app import key

logger = logging.getLogger(__name__)


class UnknownDeviceField(Exception):
    pass


class App(db.Model):
    __tablename__ = 'app'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    devices = db.relationship('Device',
                              cascade='all, delete-orphan',
                              backref='post',
                              lazy='dynamic')

    def __init__(self, name, devices=None):
        self.name = name
        if devices is not None:
            for device in devices:
                self.add_device(device)

    def get_device(self, name):
        device = next((device for device in self.devices if device.name == name), None)
        if device is not None:
            return device
        else:
            logger.warning('Cannot get device {0} for app {1}. '
                           'Device does not exist for app'.format(name, self.name))
            return None

    def get_devices_of_type(self, device_type):
        return [device for device in self.devices if device.type == device_type]

    def add_device(self, device):
        if not any(device_.name == device.name for device_ in self.devices):
            self.devices.append(device)

    def as_json(self):
        return {"name": self.name,
                "devices": [device.as_json() for device in self.devices]}

    @staticmethod
    def from_json(data):
        devices = [Device.from_json(device) for device in data['devices']] if 'devices' in data else None
        return App(data['name'], devices)


class Device(db.Model, TrackModificationsMixIn):
    __tablename__ = 'device'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    type = db.Column(db.String(25), nullable=False)
    description = db.Column(db.String(255), default='')
    plaintext_fields = db.relationship('DeviceField',
                                       cascade='all, delete-orphan',
                                       backref='post',
                                       lazy='dynamic')
    encrypted_fields = db.relationship('EncryptedDeviceField',
                                       cascade='all, delete-orphan',
                                       backref='post',
                                       lazy='dynamic')
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'))

    def __init__(self, name, plaintext_fields, encrypted_fields, device_type, description=''):
        self.name = name
        self.type = device_type
        self.description = description
        self.plaintext_fields = plaintext_fields
        self.encrypted_fields = encrypted_fields

    def get_plaintext_fields(self):
        return {field.name: field.value for field in self.plaintext_fields}

    def get_encrypted_field(self, field_name):
        field = next((field for field in self.encrypted_fields if field.name == field_name), None)
        if field is not None:
            return field.value
        else:
            raise UnknownDeviceField

    def as_json(self):
        fields_json = [field.as_json() for field in self.plaintext_fields]
        fields_json.extend([field.as_json() for field in self.encrypted_fields])
        return {"name": self.name,
                "id": self.id,
                "fields": fields_json,
                "type": self.type,
                "description": self.description}

    @staticmethod
    def _construct_fields_from_json(fields_json):
        plaintext_fields, encrypted_fields = [], []
        for field in fields_json:
            if 'encrypted' in field and field['encrypted']:
                encrypted_fields.append(EncryptedDeviceField.from_json(field))
            else:
                plaintext_fields.append(DeviceField.from_json(field))

        return plaintext_fields, encrypted_fields

    def update_from_json(self, json_in):
        if 'name' in json_in:
            self.name = json_in['name']
        if 'description' in json_in:
            self.description = json_in['description']
        if 'fields' in json_in:
            updated_plaintext_fields, updated_encrypted_fields = Device._construct_fields_from_json(json_in['fields'])

            for curr_field in self.encrypted_fields:
                for updated_field in updated_encrypted_fields:
                    if updated_field.value and updated_field.name == curr_field.name:
                        self.encrypted_fields.remove(curr_field)
                        self.encrypted_fields.append(updated_field)

            self.plaintext_fields = updated_plaintext_fields
        if 'type' in json_in:
            self.type = json_in['type']

    @staticmethod
    def from_json(json_in):
        description = json_in['description'] if 'description' in json_in else ''
        plaintext_fields, encrypted_fields = Device._construct_fields_from_json(json_in['fields'])
        return Device(json_in['name'], plaintext_fields, encrypted_fields, device_type=json_in['type'], description=description)


allowed_device_field_types = ('string', 'number', 'boolean', 'integer')


class DeviceFieldMixin(object):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    type = db.Column(db.Enum(*allowed_device_field_types))

    @declared_attr
    def device_id(cls):
        return db.Column(db.Integer, db.ForeignKey('device.id'))


class DeviceField(db.Model, DeviceFieldMixin):
    __tablename__ = 'plaintext_device_field'
    _value = db.Column('value', db.String(), nullable=False)

    def __init__(self, name, field_type, value):
        self.name = name
        self.type = field_type if field_type in allowed_device_field_types else 'string'
        self._value = str(value)

    @hybrid_property
    def value(self):
        return convert_primitive_type(self._value, self.type)

    @value.setter
    def value(self, value):
        self._value = str(value)

    def as_json(self, with_config_fields=False):
        device = {"name": self.name, "value": self.value}
        if with_config_fields:
            device["type"] = self.type
            device["encrypted"] = False
        return device

    @staticmethod
    def from_json(data):
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return DeviceField(data['name'], type_, data['value'])


class EncryptedDeviceField(db.Model, DeviceFieldMixin):
    __tablename__ = 'encrypted_device_field'
    _value = db.Column('value', db.LargeBinary(), nullable=False)

    def __init__(self, name, field_type, value):
        self.name = name
        self.type = field_type if field_type in allowed_device_field_types else 'string'
        aes = pyaes.AESModeOfOperationCTR(key)
        self._value = aes.encrypt(str(value))

    @hybrid_property
    def value(self):
        aes = pyaes.AESModeOfOperationCTR(key)
        return convert_primitive_type(aes.decrypt(self._value), self.type)

    @value.setter
    def value(self, new_value):
        aes = pyaes.AESModeOfOperationCTR(key)
        self._value = aes.encrypt(str(new_value))

    def as_json(self, with_config_fields=False):
        device = {"name": self.name, "encrypted": True}
        if with_config_fields:
            device["type"] = self.type
        return device

    @staticmethod
    def from_json(data):
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return EncryptedDeviceField(data['name'], type_, data['value'])


def get_all_devices_for_app(app_name):
    """ Gets all the devices associated with an app

    Args:
        app_name (str): The name of the app
    Returns:
        (list[Device]): A list of devices associated with this app. Returns empty list if app is not in database
    """
    app = App.query.filter_by(name=app_name).first()
    if app is not None:
        return app.devices[:]
    else:
        logger.warning('Cannot get devices for app {0}. App does not exist'.format(app_name))
        return []


def get_all_devices_of_type_from_app(app_name, device_type):
    """ Gets all the devices of a particular associated with an app

        Args:
            app_name (str): The name of the app
            device_type (str): The type of device
        Returns:
            (list[Device]): A list of devices associated with this app. Returns empty list if app is not in database
        """
    app = App.query.filter_by(name=app_name).first()
    if app is not None:
        return app.get_devices_of_type(device_type)
    else:
        logger.warning('Cannot get devices of type {0} for app {1}. App does not exist'.format(device_type, app_name))
        return []


def get_device(app_name, device_name):
    """ Gets the device associated with an app

    Args:
        app_name (str): The name of the app
        device_name (str): The name of the device
    Returns:
        (Device): The desired device. Returns None if app or device not found.
    """
    app = App.query.filter_by(name=app_name).first()
    if app is not None:
        return app.get_device(device_name)
    else:
        logger.warning('Cannot get device {0} for app {1}. App does not exist'.format(device_name, app_name))
        return None
