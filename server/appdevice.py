from sqlalchemy.ext.declarative import declared_attr, declarative_base
import pyaes
import logging
from core.helpers import format_db_path
from sqlalchemy.ext.hybrid import hybrid_property
from core.validator import convert_primitive_type
from core.config.config import secret_key as key
import core.config.paths
from sqlalchemy import Column, Integer, ForeignKey, String, create_engine, LargeBinary, Enum, DateTime, func
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

logger = logging.getLogger(__name__)

Device_Base = declarative_base()


class UnknownDeviceField(Exception):
    pass


class App(Device_Base):
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


class Device(Device_Base):
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
        return {field.name: field.value for field in self.plaintext_fields}

    def get_encrypted_field(self, field_name):
        field = next((field for field in self.encrypted_fields if field.name == field_name), None)
        if field is not None:
            return field.value
        else:
            raise UnknownDeviceField

    def as_json(self, export=False):
        fields_json = [field.as_json() for field in self.plaintext_fields]
        fields_json.extend([field.as_json(export) for field in self.encrypted_fields])
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
                    if updated_field.name == curr_field.name:
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
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    type = Column(Enum(*allowed_device_field_types))

    @declared_attr
    def device_id(cls):
        return Column(Integer, ForeignKey('device.id'))


class DeviceField(Device_Base, DeviceFieldMixin):
    __tablename__ = 'plaintext_device_field'
    _value = Column('value', String(), nullable=False)

    def __init__(self, name, field_type, value):
        self.name = name
        self.type = field_type if field_type in allowed_device_field_types else 'string'
        self._value = str(value)

    @hybrid_property
    def value(self):
        try:
            return convert_primitive_type(self._value, self.type)
        except (TypeError, ValueError):
            return self._value

    @value.setter
    def value(self, value):
        self._value = str(value)

    def as_json(self):
        return {"name": self.name, "value": self._value}

    @staticmethod
    def from_json(data):
        type_ = data['type'] if data['type'] in allowed_device_field_types else 'string'
        return DeviceField(data['name'], type_, data['value'])


class EncryptedDeviceField(Device_Base, DeviceFieldMixin):
    __tablename__ = 'encrypted_device_field'
    _value = Column('value', LargeBinary(), nullable=False)

    def __init__(self, name, field_type, value):
        self.name = name
        self.type = field_type if field_type in allowed_device_field_types else 'string'
        aes = pyaes.AESModeOfOperationCTR(key)
        self._value = aes.encrypt(str(value))

    @hybrid_property
    def value(self):
        aes = pyaes.AESModeOfOperationCTR(key)
        try:
            return convert_primitive_type(aes.decrypt(self._value), self.type)
        except (TypeError, ValueError):
            return aes.decrypt(self._value)

    @value.setter
    def value(self, new_value):
        aes = pyaes.AESModeOfOperationCTR(key)
        self._value = aes.encrypt(str(new_value))

    def as_json(self, export=False):
        field = {"name": self.name, "encrypted": True}
        if export:
            field = {"name": self.name, "value": self.value}
        return field

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
    app = device_db.session.query(App).filter(App.name == app_name).first()
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
    app = device_db.session.query(App).filter(App.name == app_name).first()
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
    app = device_db.session.query(App).filter(App.name == app_name).first()
    if app is not None:
        return app.get_device(device_name)
    else:
        logger.warning('Cannot get device {0} for app {1}. App does not exist'.format(device_name, app_name))
        return None


class DeviceDatabase(object):
    """
    Wrapper for the SQLAlchemy database object
    """

    def __init__(self):
        self.engine = create_engine(format_db_path(core.config.config.device_db_type, core.config.paths.device_db_path))
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = scoped_session(Session)

        Device_Base.metadata.bind = self.engine
        Device_Base.metadata.create_all(self.engine)


def get_device_db(_singleton=DeviceDatabase()):
    """Singleton factory which returns the database"""
    return _singleton

device_db = get_device_db()
