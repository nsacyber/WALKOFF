import os

from flask import Blueprint, render_template, request, g
#from auth import forms
from flask_security import roles_required, auth_token_required

from core import forms
from core import interface

appPage = Blueprint("appPage", "apps", template_folder=os.path.abspath('apps'), static_folder="static")


@appPage.url_value_preprocessor
def staticRequestHandler(endpoint, values):
    g.app = values.pop('app', None)
    appPage.static_folder = os.path.abspath('apps/' + g.app + '/interface/static')

@appPage.route('/display', methods=["POST"])
@auth_token_required
@roles_required("admin")
def displayApp():
    form = forms.RenderArgsForm(request.form)
    path = g.app + "/interface/templates/" + form.page.data
    args = interface.loadApp(g.app, form.key.entries, form.value.entries)

    template = render_template(path, **args)
    return template
