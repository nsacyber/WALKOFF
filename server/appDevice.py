import json
from abc import abstractmethod
from . import database
from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import relationship

db = database.db

class _App_Device(database.Base):
    __tablename__ = 'app_device'
    app_id = db.Column(Integer, ForeignKey('app.id'), primary_key=True)
    device_id = db.Column(Integer, ForeignKey('device.id'), primary_key=True)

class Device(database.Base):
    __tablename__ = 'device'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    apps = relationship('App', secondary='app_device', lazy='dynamic')
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    ip = db.Column(db.String(15))
    port = db.Column(db.Integer())

    def __init__(self, name="", app="", username="", password="", ip="0.0.0.0", port=0, apps=[]):
        self.name = name
        self.apps = apps
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port

    def as_json(self, with_apps=True):
        output = {'id' : str(self.id), 'name' : self.name, 'username' : self.username, 'ip' : self.ip, 'port' : str(self.port)}
        if with_apps:
            output['apps'] = [app.as_json() for app in self.apps]
        return output

    def add_device(self, name, apps, username, password, ip, port):
        device = Device(name=name, username=username, password=password, ip=ip, port=port)
        existing_apps = db.session.query(apps).all()
        existing_app_names = [app.app for app in existing_apps]
        for app in apps:
            if app in existing_app_names:
                for app_elem in existing_apps:
                    if app_elem in existing_apps:
                        device.apps.append(app_elem)
            else:
                print("ERROR: App is not tracked")
        db.session.add(device)
        db.session.commit()

    def filter_app_and_device(self, app_name, device_name):
        # query = Device.query.all()
        query = Device.query.filter_by(name=device_name).all()
        if query:
            for device in query:
                if device.name == device_name:
                    for app in device.apps:
                        if app.app == app_name:
                            return device
        return None

    def editDevice(self, form):
        if form.name.data:
            self.name = form.name.data

        if form.username.data:
            self.username = form.username.data

        if form.pw.data:
            self.password = form.pw.data

        if form.ipaddr.data:
            self.ip = form.ipaddr.data

        if form.port.data:
            self.port = form.port.data

        if form.app.data:
            query = App.query.all()
            if query:
                for app in query:
                    if app.app == form.app.data:
                        self.apps.append(app)

    def __repr__(self):
        return json.dumps({"name": self.name, "username": self.username, "password": self.password,
                           "ip": self.ip, "port": str(self.port), "apps": [app.as_json() for app in self.apps]})

class App(database.Base, object):
    #__metaclass__ = ABCMeta

    __tablename__ = 'app'
    id = db.Column(Integer, primary_key=True)
    app = db.Column(String)
    devices = relationship('Device', secondary='app_device', lazy='dynamic')

    def as_json(self, with_devices=False):
        output = {'id' : str(self.id), 'app' : self.app}
        if with_devices:
            output['devices'] = [device.as_json() for device in self.devices]
        return output


    def __init__(self, app=None, devices=None):
        self.app = app
        if devices is not None:
            for device in devices:
                self.getConfig(device)

    def getConfig(self, device):

        if device:
            query = dev_class.filter_app_and_device(app_name=self.app, device_name=device)
            if query:
                self.config = query

        else:
            self.config = {}

    @abstractmethod
    def shutdown(self):
        return

dev_class = Device()
