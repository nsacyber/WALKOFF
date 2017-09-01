import os
import sys
import importlib
from flask import Blueprint, render_template, request, g, current_app
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from server import forms

widget_page = Blueprint('widgetPage', 'apps', template_folder=os.path.abspath('apps'), static_folder='static')


@widget_page.url_value_preprocessor
def static_request_handler(endpoint, values):
    g.app = values.pop('app', None)
    g.widget = values.pop('widget', None)
    widget_page.static_folder = os.path.abspath(os.path.join('apps', g.app, 'widgets', g.widget, 'static'))


@widget_page.route('/display', methods=['POST'])
@jwt_required
@roles_accepted('admin')
def display_app():
    form = forms.RenderArgsForm(request.form)
    path = '{0}/widgets/{1}/templates/{2}'.format(g.app, g.widget, form.page.data)
    args = load_widget(g.app, g.widget, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template


def load_module(app_name, widget_name):
    module = 'apps.{0}.widgets.{1}.display'.format(app_name, widget_name)
    try:
        return sys.modules[module]
    except KeyError:
        pass
    try:
        return importlib.import_module(module, '')
    except ImportError:
        current_app.logger.error('Could not load widget module {0} for app {1}'.format(widget_name, app_name))
        return None


def load_widget(app_name, widget_name, keys, values):
    module = load_module(app_name, widget_name)
    args = dict(zip(keys, values))
    return getattr(module, 'load')(args) if module else {}
