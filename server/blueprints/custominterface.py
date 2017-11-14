import os

from flask import Blueprint, render_template, g
from flask_jwt_extended import jwt_required

custom_interface_page = Blueprint('custom_interface', 'interfaces', template_folder=os.path.abspath('interfaces'), static_folder='static')


@custom_interface_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.interface = values.pop('interface', None)
    static_path = os.path.abspath(os.path.join('interfaces', g.interface, 'interface', 'static'))
    custom_interface_page.static_folder = static_path


@custom_interface_page.route('/', methods=['GET'])
@jwt_required
def read_app():
    path = '{}/interface/templates/index.html'.format(g.interface)
    return render_template(path)

