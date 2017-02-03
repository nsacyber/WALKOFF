import os, ssl, json

from flask import Flask, jsonify, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask_security import auth_token_required, current_user, roles_required
from flask_security.utils import encrypt_password, verify_and_update_password

from jinja2 import Environment, FileSystemLoader

from core import config, appBlueprint, interface

app = Flask(__name__, static_folder=os.path.abspath('server/static'))

app.jinja_loader = FileSystemLoader(['server/templates'])

app.register_blueprint(appBlueprint.appPage, url_prefix='/apps/<app>')

app.config.update(
        #CHANGE SECRET KEY AND SECURITY PASSWORD SALT!!!
        SECRET_KEY = "SHORTSTOPKEYTEST",
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath(config.dbPath),
        SECURITY_PASSWORD_HASH = 'pbkdf2_sha512',
        SECURITY_TRACKABLE = False,
        SECURITY_PASSWORD_SALT = 'something_super_secret_change_in_production',
        SECURITY_POST_LOGIN_VIEW = '/',
        WTF_CSRF_ENABLED = False
    )

#Template Loader
env = Environment(loader=FileSystemLoader("apps"))

app.config["SECURITY_LOGIN_USER_TEMPLATE"] = "login_user.html"


#Database Connection Object
db = SQLAlchemy(app)

#Base Class for Tables
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

#Define Models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('auth_user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('auth_role.id')))

class Role(Base, RoleMixin):
    __tablename__ = 'auth_role'
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def setDescription(self, description):
        self.description = description

    def toString(self):
        return {"name" : self.name, "description" : self.description}

    def __repr__(self):
        return '<Role %r>' % self.name

class User(Base, UserMixin):
    __tablename__ = 'auth_user'
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))


    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer)

    def display(self):
        result = {}
        result["username"] = self.email
        roles = []
        for role in self.roles:
            roles.append(role.toString())
        result["roles"] = roles
        result["active"] = self.active

        return result

    def setRoles(self, roles):
        for role in roles:
            if role.data != "" and not self.has_role(role.data):
                q = user_datastore.find_role(role.data)
                if q != None:
                    user_datastore.add_role_to_user(self, q)
                    print("ADDED ROLE")
                else:
                    print("ROLE DOES NOT EXIST")
            else:
                print("HAS ROLE")

    def __repr__(self):
        return '<User %r>' % self.email

#Setup Flask Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

#Creates Test Data
@app.before_first_request
def create_user():
    #db.drop_all()
    db.create_all()
    if not User.query.first():
        #Add Credentials to Splunk app
        #db.session.add(Device(name="deviceOne", app="splunk", username="admin", password="hello", ip="192.168.0.1", port="5000"))

        adminRole = user_datastore.create_role(name="admin", description="administrator")
        #userRole = user_datastore.create_role(name="user", description="user")

        u = user_datastore.create_user(email='admin', password=encrypt_password('admin'))
        #u2 = user_datastore.create_user(email='user', password=encrypt_password('user'))

        user_datastore.add_role_to_user(u, adminRole)

        db.session.commit()


@app.route("/")
@login_required
def default():
    if current_user.is_authenticated:
        args = {"apps": config.getApps(), "authKey": current_user.get_auth_token(), "currentUser": current_user.email}
        return render_template("container.html", **args)
    else:
        return {"status": "Could Not Log In."}


@app.route("/workflow/", methods=['GET'])
def workflow():
    return ""



#Returns System-Level Interface Pages
@app.route('/interface/<string:name>/display', methods=["POST"])
@auth_token_required
@roles_required("admin")
def systemPages(name):
    if current_user.is_authenticated and name:
        args, form = getattr(interface, name)()
        return render_template("pages/" + name + "/index.html", form=form, **args)
    else:
        return {"status" : "Could Not Log In."}

#Start Flask
def start(config_type=None):
    global db, env

    if config.authConfig["https"].lower() == "true":
        #Sets up HTTPS
        if config.authConfig["TLS_version"] == "1.2":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        elif config.authConfig["TLS_version"] == "1.1":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        #Provide user with informative error message
        displayIfFileNotFound(config.authConfig["certificatePath"])
        displayIfFileNotFound(config.authConfig["privateKeyPath"])

        context.load_cert_chain(config.authConfig["certificatePath"], config.authConfig["privateKeyPath"])
        app.run(debug=config.interfaceConfig["debug"], ssl_context=context, host=config.interfaceConfig["host"], port=int(config.interfaceConfig["port"]),threaded=True)
    else:
        app.run(debug=config.interfaceConfig["debug"], host=config.interfaceConfig["host"], port=int(config.interfaceConfig["port"]),threaded=True)

def displayIfFileNotFound(filepath):
    if not os.path.isfile(filepath):
        print("File not found: " + filepath)
