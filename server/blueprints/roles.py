import json
from flask import Blueprint, request, current_app
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context, default_urls
from server import forms
from server.database import add_to_user_roles

roles_page = Blueprint('roles_page', __name__)


# Returns the list of all user roles
@roles_page.route('', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def display_roles():
    roles = running_context.Role.query.all()
    if roles:
        result = [role.name for role in roles]
        return json.dumps(result)
    else:
        current_app.logger.error('Cannot display roles. No roles exist.')
        return json.dumps({"status": "roles do not exist"})


@roles_page.route('/<string:role_name>', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def create_role(role_name):
    form = forms.NewRoleForm(request.form)
    if form.validate():
        if not running_context.Role.query.filter_by(name=role_name).first():

            if form.description.data is not None:
                description = form.description.data
                running_context.user_datastore.create_role(name=role_name, description=description, pages=default_urls)
            else:
                description = ''
                running_context.user_datastore.create_role(name=role_name, pages=default_urls)

            add_to_user_roles(role_name, default_urls)

            running_context.db.session.commit()
            current_app.logger.info('Role added: {0}'.format(json.dumps({"name": role_name,
                                                                         "description": description,
                                                                         "urls": default_urls})))
            return json.dumps({"status": "role added " + role_name})
        else:
            current_app.logger.warning('Cannot add role {0}. Role already exists'.format(role_name))
            return json.dumps({"status": "role exists"})
    else:
        current_app.logger.error('Input invalid to create a role.')
        return json.dumps({"status": "invalid input"})


@roles_page.route('/<string:role_name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def get_role(role_name):
    role = running_context.Role.query.filter_by(name=role_name).first()
    if role:
        return json.dumps(role.display())
    else:
        current_app.logger.error('Cannot display role {0}. Role does not exist.'.format(role_name))
        return json.dumps({"status": "role does not exist"})


@roles_page.route('/<string:role_name>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def edit_role(role_name):
    role = running_context.Role.query.filter_by(name=role_name).first()
    if role:
        form = forms.EditRoleForm(request.form)
        if form.validate():
            if form.description.data:
                role.set_description(form.description.data)
            if form.pages.data:
                add_to_user_roles(role_name, form.pages)
        current_app.logger.info('Edited role {0} to {1}'.format(role_name,
                                                                json.dumps({"name": role_name,
                                                                            "description": form.description.data,
                                                                            "urls": form.pages.data})))
        return json.dumps(role.display())
    else:
        current_app.logger.error('Cannot edit role {0}. Role does not exist.'.format(role_name))
        return json.dumps({"status": "role does not exist"})
