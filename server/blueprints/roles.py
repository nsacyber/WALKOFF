import json
from flask import Blueprint, request
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
        return json.dumps({"status": "roles do not exist"})


@roles_page.route('/<string:role_name>', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def create_role(role_name):
    form = forms.NewRoleForm(request.form)
    if form.validate():
        if not running_context.Role.query.filter_by(name=role_name).first():

            if form.description.data is not None:
                d = form.description.data
                running_context.user_datastore.create_role(name=role_name, description=d, pages=default_urls)
            else:
                running_context.user_datastore.create_role(name=role_name, pages=default_urls)

            add_to_user_roles(role_name, default_urls)

            running_context.db.session.commit()
            return json.dumps({"status": "role added " + role_name})
        else:
            return json.dumps({"status": "role exists"})
    else:
        return json.dumps({"status": "invalid input"})

@roles_page.route('/<string:role_name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def get_role(role_name):
    role = running_context.Role.query.filter_by(name=role_name).first()
    if role:
        return json.dumps(role.display())
    else:
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
        return json.dumps(role.display())
    else:
        return json.dumps({"status": "role does not exist"})

#TODO: DELETE
@roles_page.route('/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def role_add_actions(action):
    # Adds a new role
    if action == 'add':
        form = forms.NewRoleForm(request.form)
        if form.validate():
            if not running_context.Role.query.filter_by(name=form.name.data).first():
                n = form.name.data

                if form.description.data is not None:
                    d = form.description.data
                    running_context.user_datastore.create_role(name=n, description=d, pages=default_urls)
                else:
                    running_context.user_datastore.create_role(name=n, pages=default_urls)

                add_to_user_roles(n, default_urls)

                running_context.db.session.commit()
                return json.dumps({"status": "role added " + n})
            else:
                return json.dumps({"status": "role exists"})
        else:
            return json.dumps({"status": "invalid input"})
    else:
        return json.dumps({"status": "invalid input"})


#TODO: DELETE
@roles_page.route('/<string:action>/<string:name>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/roles'])
def role_actions(action, name):
    role = running_context.Role.query.filter_by(name=name).first()
    if role:
        if action == 'edit':
            form = forms.EditRoleForm(request.form)
            if form.validate():
                if form.description.data:
                    role.set_description(form.description.data)
                if form.pages.data:
                    add_to_user_roles(name, form.pages)
            return json.dumps(role.display())

        elif action == 'display':
            return json.dumps(role.display())
        else:
            return json.dumps({"status": "invalid input"})

    return json.dumps({"status": "role does not exist"})



