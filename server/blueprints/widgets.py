import os

from flask import Blueprint, render_template, g
from flask_jwt_extended import jwt_required

widgets_page = Blueprint('widgetsPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')


@widgets_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.app = values.pop('app', None)
    g.widget = values.pop('widget', None)
    widgets_page.static_folder = os.path.abspath(os.path.join('apps', g.app, 'widgets', g.widget, 'static'))


@widgets_page.route('', methods=['POST'])
@jwt_required
def display_app():
    path = '{0}/widgets/{1}/templates/index.html'.format(g.app, g.widget)
    return render_template(path)
