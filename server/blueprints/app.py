import os
from flask import Blueprint, render_template, g
from flask_jwt_extended import jwt_required

app_page = Blueprint('appPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')


@app_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.app = values.pop('app', None)
    app_page.static_folder = os.path.abspath(os.path.join('apps', g.app, 'interface', 'static'))


@app_page.route('/', methods=['GET'])
@jwt_required
def read_app():
    path = '{}/interface/templates/index.html'.format(g.app)
    return render_template(path)
