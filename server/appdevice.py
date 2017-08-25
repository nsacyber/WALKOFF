from flask import current_app
from sqlalchemy import Integer, String
from sqlalchemy.ext.declarative import declared_attr
import pyaes
import logging
from server.database import Base, db
from sqlalchemy.ext.hybrid import hybrid_property
from core.validator import convert_primitive_type
from server.app import key

logger = logging.getLogger(__name__)


class UnknownDeviceField(Exception):
    pass


class App(Base):
    __tablename__ = 'app'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(25), nullable=False, unique=True)
    devices = db.relationship('Device',
                              cascade='all, delete-orphan',
                              backref='post',
                              lazy='dynamic')

    def __init__(self, name, devices_json=None):
        self.name = name
        if devices_json is not None:
            for device in devices_json:
                self.devices.append(Device.from_json(device))

    def get_device(self, name):
        device = next((device for device in self.devices if device.name == name), None)
        if device is not None:
            return device
        else:
            logger.warning('Cannot get device {0} for app {1}. '
                           'Device does not exist for app'.format(name, self.name))
            return None

    def as_json(self):
        return {"name": self.name,
                "devices": [device.as_json() for device in self.devices]}

    @staticmethod
    def from_json(data):
        devices = data['devices'] if 'devices' in data else None
        return App(data['name'], devices)


def get_all_devices_for_app(app_name):
    """ Gets all the devices associated with an app

    Args:
        app_name (str): The name of the app
    Returns:
        (list[Device]): A list of devices associated with this app. Returns empty list if app is not in database
    """
    app = App.query.filter_by(name=app_name).first()
    if app is not None:
        return app.devices
    else:
        logger.warning('Cannot get devices for app {0}. App does not exist'.format(app_name))
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


class Device(Base):
    __tablename__ = 'device'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(25), nullable=False, unique=True)
    plaintext_fields = db.relationship('DeviceField',
                                       cascade='all, delete-orphan',
                                       backref='post',
                                       lazy='dynamic')
    encrypted_fields = db.relationship('EncryptedDeviceField',
                                       cascade='all, delete-orphan',
                                       backref='post',
                                       lazy='dynamic')
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'))

    def __init__(self, name, fields_json):
        self.name = name
        for field in fields_json:
            if not field['encrypted']:
                self.plaintext_fields.append(DeviceField.from_json(field))
            else:
                self.encrypted_fields.append(EncryptedDeviceField.from_json(field))

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
                "fields": fields_json}

    @staticmethod
    def from_json(data):
        return Device(data['name'], data['fields'])


allowed_device_field_types = ('string', 'number', 'boolean', 'integer')


class DeviceFieldMixin(object):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(25), nullable=False, unique=True)
    type = db.Column(db.Enum(*allowed_device_field_types))

    @declared_attr
    def device_id(cls):
        return db.Column(db.Integer, db.ForeignKey('device.id'))


class DeviceField(DeviceFieldMixin, Base):
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

    def as_json(self):
        return {"name": self.name, "value": self.value, "type": self.type, "encrypted": False}

    @staticmethod
    def from_json(data):
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return DeviceField(data['name'], type_, data['value'])


class EncryptedDeviceField(DeviceFieldMixin, Base):
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

    def as_json(self):
        return {"name": self.name, "type": self.type, "encrypted": True}

    @staticmethod
    def from_json(data):
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return EncryptedDeviceField(data['name'], type_, data['value'])
