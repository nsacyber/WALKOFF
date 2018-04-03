import logging
import os

from flask import render_template, send_from_directory

import walkoff.config
from walkoff.server import app
from sqlalchemy.exc import SQLAlchemyError
from walkoff.server.problem import Problem
from walkoff.server.returncodes import SERVER_ERROR

logger = logging.getLogger(__name__)


# Custom static data
@app.route('/client/<path:filename>')
def client_app_folder(filename):
    return send_from_directory(os.path.abspath(walkoff.config.Config.CLIENT_PATH), filename)


@app.route('/')
@app.route('/playbook')
@app.route('/execution')
@app.route('/scheduler')
@app.route('/devices')
@app.route('/messages')
@app.route('/cases')
@app.route('/metrics')
@app.route('/settings')
def default():
    return render_template("index.html")


@app.route('/interfaces/<interface_name>')
def app_page(interface_name):
    return render_template("index.html")


@app.route('/login')
def login_page():
    return render_template("login.html")


@app.errorhandler(SQLAlchemyError)
def handle_database_errors(e):
    return Problem(SERVER_ERROR, 'A database error occurred.', e.__class__.__name__)


@app.errorhandler(500)
def handle_generic_server_error(e):
    return Problem(SERVER_ERROR, 'An error occurred in the server.', e.__class__.__name__)
