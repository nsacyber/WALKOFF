import os

from flask import Blueprint, render_template, g
from flask_jwt_extended import jwt_required

app_interface_page = Blueprint('app_interface_page', 'interfaces',
                               template_folder=os.path.abspath('interfaces'), static_folder='static')


@app_interface_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.appinterface = values.pop('interface', None)
    app_interface_page.static_folder = os.path.abspath(
        os.path.join('interfaces', g.appinterface, 'interface', 'static'))


@app_interface_page.route('/', methods=['GET'])
@jwt_required
def read_app():
    path = '{}/interface/templates/index.html'.format(g.appinterface)
    return render_template(path)
