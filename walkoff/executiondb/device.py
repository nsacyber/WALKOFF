import logging
import sys

from sqlalchemy import Column, Integer, ForeignKey, String, LargeBinary, Enum, DateTime, func, orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from walkoff import executiondb
from walkoff.appgateway.validator import convert_primitive_type
from walkoff.executiondb import Execution_Base, ExecutionDatabase

import nacl.secret
import nacl.utils
import os
import zmq.auth as auth
import walkoff.config

logger = logging.getLogger(__name__)


class UnknownDeviceField(Exception):
    pass


class App(Execution_Base):
    """SqlAlchemy ORM class for Apps

    Attributes:
        id (int): Integer Column which is the primary key
        name (str): String Column which is the name of the app
        devices: One-to-many relationship to Devices

    Args:
        name (str): Name of the app
        devices (iterable(Device), optional): The devices for this app . Defaults to None
    """
    __tablename__ = 'app'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), nullable=False)
    devices = relationship('Device',
                           cascade='all, delete-orphan',
                           backref='post',
                           lazy='dynamic')

    def __init__(self, name, devices=None):
        self.name = name
        if devices is not None:
            for device in devices:
                self.add_device(device)

    def get_device(self, device_id):
        """Gets a device associated with this app by ID

        Args:
            device_id (int): The device's ID

        Returns:
            Device: The Device with the given ID if found. None otherwise
        """
        device = next((device for device in self.devices if device.id == device_id), None)
        if device is not None:
            return device
        else:
            logger.warning('Cannot get device {0} for app {1}. '
                           'Device does not exist for app'.format(device_id, self.name))
            return None

    def get_devices_of_type(self, device_type):
        """Gets all the devices associated with this app of a given type

        Args:
            device_type (str): The device type to get

        Returns:
            list[Device]: All the devices associated with this app which have the given device type
        """
        return [device for device in self.devices if device.type == device_type]

    def add_device(self, device):
        """Adds a device to this app.
        If the name of the device to add to this app already exists, then no device will be added

        Args:
            device (Device): The device to add
        """
        if not any(device_.name == device.name for device_ in self.devices):
            self.devices.append(device)

    def as_json(self, with_devices=False):
        """Gets the JSON representation of an App object.

        Args:
            with_devices (bool, optional): Should the devices of this app be included in its JSON? Defaults to False

        Returns:
            dict: The JSON representation of an App object.
        """
        output = {'name': self.name}
        if with_devices:
            output['devices'] = [device.as_json() for device in self.devices]
        return output

    @staticmethod
    def from_json(data):
        """Constructs an App from its JSON representation

        Args:
            data (dict): The JSON representation of the App

        Returns:
            apps.devicedb.App: The constructed app
        """
        devices = [Device.from_json(device) for device in data['devices']] if 'devices' in data else None
        return App(data['name'], devices)


class Device(Execution_Base):
    """The SqlAlchemy ORM class for a Device

    Attributes:
        id (int): The id of this device. The primary key in the table
        name (str): The name of this device
        type (str): The type of this device
        description (str): A brief description of what this device represents
        plaintext_fields: A relationship to a DeviceField table
        encrypted_fields: A relationship to an EncryptedDeviceField table
        app_id (int): Foreign key to the app which is associated with this device.
        created_at (datetime): The time this device was created at
        modified_at (datetime): The time this device was last modified

    Args:
        name (str): The name of this device
        plaintext_fields (list[DeviceField]): The plaintext fields for this device
        encrypted_fields (list[EncryptedDeviceField]): The encrypted fields for this device
        device_type (str): The type of this device
        description: (str, optional): This device's description. Defaults to empty string
    """
    __tablename__ = 'device'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), nullable=False)
    type = Column(String(25), nullable=False)
    description = Column(String(255), default='')
    plaintext_fields = relationship('DeviceField',
                                    cascade='all, delete-orphan',
                                    backref='post',
                                    lazy='dynamic')
    encrypted_fields = relationship('EncryptedDeviceField',
                                    cascade='all, delete-orphan',
                                    backref='post',
                                    lazy='dynamic')
    app_id = Column(Integer, ForeignKey('app.id'))
    created_at = Column(DateTime, default=func.current_timestamp())
    modified_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    def __init__(self, name, plaintext_fields, encrypted_fields, device_type, description=''):
        self.name = name
        self.type = device_type
        self.description = description
        self.plaintext_fields = plaintext_fields
        self.encrypted_fields = encrypted_fields

    def get_plaintext_fields(self):
        """Gets all the plaintext fields associated with this device

        Returns:
            dict{str: str|int|bool|float}: All the plaintext fields associated with this device.
                In the form of {field_name: value}
        """
        return {field.name: field.value for field in self.plaintext_fields}

    def get_encrypted_field(self, field_name):
        """Gets an encrypted field

        Args:
            field_name (str): The name of the encrypted field to get

        Returns:
            The encrypted field

        Raises:
            UnknownDeviceField: If the device does not have an encrypted field with this name
        """
        field = next((field for field in self.encrypted_fields if field.name == field_name), None)
        if field is not None:
            return field.value
        else:
            raise UnknownDeviceField

    def as_json(self, export=False):
        """Constructs a JSON representation of this object

        Args:
            export (bool, optional): Should the value of all the encrypted device field be sent? Defaults to False

        Returns:
            dict: The JSON representation of this device
        """
        fields_json = [field.as_json() for field in self.plaintext_fields]
        fields_json.extend([field.as_json(export) for field in self.encrypted_fields])
        return {"name": self.name,
                "id": self.id,
                "fields": fields_json,
                "type": self.type,
                "description": self.description}

    @staticmethod
    def _construct_fields_from_json(fields_json):
        """Constructs DeviceFields and EncryptedDeviceFields from their JSON representation

        Args:
            fields_json (list[dict]): List of the JSON represnetaion of the device fields

        Returns:
            tuple(list[DeviceField], list[EncryptedDeviceField]): The constructed device fields
        """
        plaintext_fields, encrypted_fields = [], []
        for field in fields_json:
            if 'encrypted' in field and field['encrypted']:
                encrypted_fields.append(EncryptedDeviceField.from_json(field))
            else:
                plaintext_fields.append(DeviceField.from_json(field))

        return plaintext_fields, encrypted_fields

    def update_from_json(self, json_in, complete_object):
        """Updates this device from a partial JSON representation of a Device

        Args:
            json_in (dict): The partial JSON representation of a Device
            complete_object (bool): Whether or not this is a PUT or PATCH
        """
        if 'name' in json_in:
            self.name = json_in['name']
        if 'description' in json_in:
            self.description = json_in['description']
        if 'fields' in json_in:
            updated_plaintext_fields, updated_encrypted_fields = Device._construct_fields_from_json(json_in['fields'])

            if complete_object:
                self.plaintext_fields = updated_plaintext_fields
                self.encrypted_fields = updated_encrypted_fields
            else:
                updated_plaintext_names = [field.name for field in updated_plaintext_fields]
                self.plaintext_fields = [field for field in self.plaintext_fields if
                                         field.name not in updated_plaintext_names]
                for field in updated_plaintext_fields:
                    self.plaintext_fields.append(field)

                updated_encrypted_names = [field.name for field in updated_encrypted_fields]
                self.encrypted_fields = [field for field in self.encrypted_fields if
                                         field.name not in updated_encrypted_names]
                for field in updated_encrypted_fields:
                    self.encrypted_fields.append(field)

        if 'type' in json_in:
            self.type = json_in['type']

    @staticmethod
    def from_json(json_in):
        """Constructs a Device from its JSON representation

        Args:
            json_in (dict): A JSON representation of a Device

        Returns:
            Device: The constructed device
        """
        description = json_in['description'] if 'description' in json_in else ''
        plaintext_fields, encrypted_fields = Device._construct_fields_from_json(json_in['fields'])
        return Device(
            json_in['name'], plaintext_fields, encrypted_fields, device_type=json_in['type'], description=description)


allowed_device_field_types = ('string', 'number', 'boolean', 'integer')
"""tuple: The string representations from JSON Schema of the allowed fields to be stored in a DeviceField
"""


class DeviceFieldMixin(object):
    """A mixin for DeviceFields which adds a primary key, name, and type

    Attributes:
        id (int): The primary key of this table
        name (str): The name of the device field
        type (str): The data type of this device field. Must come from allowed_device_field_types

    """
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    type = Column(Enum(*allowed_device_field_types))

    @declared_attr
    def device_id(cls):
        return Column(Integer, ForeignKey('device.id'))


class DeviceField(Execution_Base, DeviceFieldMixin):
    """The SqlAlchemy ORM for an unencrypted DeviceField

    Attributes:
        value (str|int|bool|float): The value of the field. This is stored as a string and cast back to the appropriate
            type when accessed

    Args:
        name (str): The name of the device field
        field_type (str): The type of the field. Must come from allowed_device_field_types else it will be cast to a
            string
        value (int|str|bool|float): The value of this field
    """
    __tablename__ = 'plaintext_device_field'
    _value = Column('value', String(), nullable=False)

    def __init__(self, name, field_type, value):
        self.name = name
        self.type = field_type if field_type in allowed_device_field_types else 'string'
        self._value = str(value)

    @hybrid_property
    def value(self):
        if self._value == '':
            return self._value
        elif self._value == 'None':
            return None
        else:
            return convert_primitive_type(self._value, self.type)

    @value.setter
    def value(self, value):
        self._value = str(value)

    def as_json(self):
        """Gets a JSON representation of this object

        Returns:
            dict: The JSON representation of this object
        """
        return {"name": self.name, "type": self.type, "value": self.value, "encrypted": False}

    @staticmethod
    def from_json(data):
        """Constructs a DeviceField from its JSON representation

        Args:
            data (dict): The JSON representation of a DeviceField

        Returns:
            DeviceField: The constructed DeviceField
        """
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return DeviceField(data['name'], type_, data['value'])


class EncryptedDeviceField(Execution_Base, DeviceFieldMixin):
    """The SqlAlchemy ORM for an encrypted DeviceField

    Attributes:
        value (str|int|bool|float): The value of the field. This is stored as an encrypted string. When accessed it is
            decrypted and cast back to the appropriate type
    Args:
        name (str): The name of the device field
        field_type (str): The type of the field. Must come from allowed_device_field_types else it will be cast to a
            string
        value (int|str|bool|float): The value of this field
    """
    __tablename__ = 'encrypted_device_field'
    _value = Column('value', LargeBinary(), nullable=False)

    def __init__(self, name, field_type, value):
        self.name = name
        self.type = field_type if field_type in allowed_device_field_types else 'string'

        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        _, server_secret = auth.load_certificate(server_secret_file)
        self.__key = server_secret[:nacl.secret.SecretBox.KEY_SIZE]
        self.__box = nacl.secret.SecretBox(self.__key)
        self._value = self.__box.encrypt(str(value).encode('utf-8'))

    @orm.reconstructor
    def init_on_load(self):
        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        _, server_secret = auth.load_certificate(server_secret_file)
        self.__key = server_secret[:nacl.secret.SecretBox.KEY_SIZE]
        self.__box = nacl.secret.SecretBox(self.__key)

    @hybrid_property
    def value(self):
        is_py2 = sys.version_info[0] == 2
        none_string = 'None' if is_py2 else b'None'

        val = self.__box.decrypt(self._value)
        if val is None or val == none_string:
            return None
        elif not val:
            return val
        else:
            if not is_py2:
                val = val.decode('utf-8')
            return convert_primitive_type(val, self.type)

    @value.setter
    def value(self, new_value):
        self._value = self.__box.encrypt(str(new_value).encode('utf-8'))

    def as_json(self, export=False):
        """Gets a JSON representation of this object

        Args:
            export (bool, optional): Should the value be decrypted and returned? Defaults to False

        Returns:
            dict: The JSON representation of this object
        """
        field = {"name": self.name, "type": self.type, "encrypted": True}
        if export:
            field = {"name": self.name, "type": self.type, "value": self.value}
        return field

    @staticmethod
    def from_json(data):
        """Constructs a DeviceField from its JSON representation

        Args:
            data (dict): The JSON representation of a DeviceField

        Returns:
            DeviceField: The constructed DeviceField
        """
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return EncryptedDeviceField(data['name'], type_, data['value'])


def get_all_devices_for_app(app_name):
    """ Gets all the devices associated with an app

    Args:
        app_name (str): The name of the app
    Returns:
        list[Device]: A list of devices associated with this app. Returns empty list if app is not in database
    """
    execution_db = ExecutionDatabase.instance
    app = execution_db.session.query(App).filter(App.name == app_name).first()
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
            list[Device]: A list of devices associated with this app. Returns empty list if app is not in database
        """
    execution_db = ExecutionDatabase.instance
    app = execution_db.session.query(App).filter(App.name == app_name).first()
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
        Device: The desired device. Returns None if app or device not found.
    """
    execution_db = ExecutionDatabase.instance
    app = execution_db.session.query(App).filter(App.name == app_name).first()
    if app is not None:
        return app.get_device(device_name)
    else:
        logger.warning('Cannot get device {0} for app {1}. App does not exist'.format(device_name, app_name))
        return None


def get_app(app_name):
    """ Gets the app associated with an app name

    Args:
        app_name (str): The name of the app
    Returns:
        apps.devicedb.App: The desired device. Returns None if app or device not found.
    """
    execution_db = ExecutionDatabase.instance
    app = execution_db.session.query(App).filter(App.name == app_name).first()
    if app is not None:
        return app
    else:
        logger.warning('Cannot get app {}. App does not exist'.format(app_name))
        return None
