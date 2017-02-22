import os

from flask import Flask
from jinja2 import Environment, FileSystemLoader

from core import config, appBlueprint

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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
