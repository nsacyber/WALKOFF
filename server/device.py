from server import database
import json

db = database.db

class Device(database.Base):
    __tablename__ = 'devices'

    name = db.Column(db.String(80), unique=True)
    app = db.Column(db.String(80))
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    ip = db.Column(db.String(15))
    port = db.Column(db.Integer())

    def __init__(self, name="", app="", username="", password="", ip="0.0.0.0", port=0, other=""):
        self.name = name
        self.app = app
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.other = other

    def editDevice(self, form):
        if form.name.data != "" and form.name.data != None:
            self.name = form.name.data

        if form.username.data != "" and form.username.data != None:
            self.username = form.username.data

        if form.pw.data != "" and form.pw.data != None:
            self.password = form.pw.data

        if form.ipaddr.data != "" and form.ipaddr.data != None:
            self.ip = form.ipaddr.data

        if form.port.data != "" and form.port.data != None:
            self.port = form.port.data

    def __repr__(self):
        return json.dumps({"name" : self.name, "app" : self.app, "username" : self.username, "password" : self.password,
                           "ip" : self.ip, "port" : str(self.port)})