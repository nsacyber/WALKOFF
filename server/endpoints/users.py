import json
from flask import Blueprint, request, current_app
from flask_security import auth_token_required, roles_accepted
from flask_security.utils import encrypt_password
from server.flaskserver import running_context, current_user
from server import forms


users_page = Blueprint('users_page', __name__)


# Controls non-specific users and roles
@users_page.route('/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def display_users():
    result = str(running_context.User.query.all())
    return json.dumps(result)


@users_page.route('/<string:username>', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def add_user(username):
    form = forms.NewUserForm(request.form)
    if form.validate():
        if not running_context.User.query.filter_by(email=username).first():
            un = username
            pw = encrypt_password(form.password.data)

            # Creates User
            u = running_context.user_datastore.create_user(email=un, password=pw)

            if form.role.data:
                u.set_roles(form.role.data)

            has_admin = False
            for role in u.roles:
                if role.name == 'admin':
                    has_admin = True
            if not has_admin:
                u.set_roles(['admin'])

            running_context.db.session.commit()
            current_app.logger.info('User added: {0}'.format(json.dumps({"name": username, "roles": [str(_role) for _role in u.roles]})))
            return json.dumps({"status": "user added " + str(u.id)})
        else:
            current_app.logger.warning('Could not create user {0}. user already exists'.format(username))
            return json.dumps({"status": "user exists"})
    else:
        current_app.logger.error('Could not add user {0}. Invalid form'.format(username))
        return json.dumps({"status": "invalid input"})


@users_page.route('/<string:username>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def read_user(username):
    user = running_context.user_datastore.get_user(username)
    if user:
        return json.dumps(user.display())
    else:
        current_app.logger.error('Could not display user {0}. User does not exist'.format(username))
        return json.dumps({"status": "could not display user"})


@users_page.route('/<string:username>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def update_user(username):
    user = running_context.user_datastore.get_user(username)
    if user:
        form = forms.EditUserForm(request.form)
        if form.validate():
            if form.password:
                user.password = encrypt_password(form.password.data)
                running_context.db.session.commit()
            if form.role.data:
                user.set_roles(form.role.data)
        current_app.logger.info('Updated user {0}. Roles: {1}'.format(username, form.role.data))
        return json.dumps(user.display())
    else:
        current_app.logger.error('Could not edit user {0}. User does not exist'.format(username))
        return json.dumps({"status": "could not edit user"})


@users_page.route('/<string:username>', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def delete_user(username):
    user = running_context.user_datastore.get_user(username)
    if user:
        if user != current_user:
            running_context.user_datastore.delete_user(user)
            running_context.db.session.commit()
            current_app.logger.info('User {0} deleted'.format(username))
            return json.dumps({"status": "user removed"})
        else:
            current_app.logger.error('Could not delete user {0}. User is current user.'.format(username))
            return json.dumps({"status": "user could not be removed"})
    else:
        current_app.logger.error('Could not delete user {0}. Form invalid'.format(username))
        return json.dumps({"status": "user could not be removed"})
