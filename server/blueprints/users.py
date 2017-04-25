import json
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from flask_security.utils import encrypt_password
from server.flaskserver import running_context, current_user
from server import forms


users_page = Blueprint('users_page', __name__)


# Controls non-specific users and roles
@users_page.route('/', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def display_all_users():
    result = str(running_context.User.query.all())
    return json.dumps(result)


# Controls non-specific users and roles
@users_page.route('/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def user_non_specific_actions(action):
    # Adds a new user
    if action == 'add':
        form = forms.NewUserForm(request.form)
        if form.validate():
            if not running_context.User.query.filter_by(email=form.username.data).first():
                un = form.username.data
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
                return json.dumps({"status": "user added " + str(u.id)})
            else:
                return json.dumps({"status": "user exists"})
        else:
            return json.dumps({"status": "invalid input"})


# Controls non-specific users and roles
@users_page.route('/<string:id_or_email>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def display_user(id_or_email):
    user = running_context.user_datastore.get_user(id_or_email)
    if user:
        return json.dumps(user.display())
    else:
        return json.dumps({"status": "could not display user"})


# Controls users and roles
@users_page.route('/<string:id_or_email>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/users'])
def user_actions(action, id_or_email):
    user = running_context.user_datastore.get_user(id_or_email)
    if user:
        if action == 'remove':
            if user != current_user:
                running_context.user_datastore.delete_user(user)
                running_context.db.session.commit()
                return json.dumps({"status": "user removed"})
            else:
                return json.dumps({"status": "user could not be removed"})

        elif action == 'edit':
            form = forms.EditUserForm(request.form)
            if form.validate():
                if form.password:
                    user.password = encrypt_password(form.password.data)
                    running_context.db.session.commit()
                if form.role.data:
                    user.set_roles(form.role.data)

            return json.dumps(user.display())

        elif action == 'display':
            if user is not None:
                return json.dumps(user.display())
            else:
                return json.dumps({"status": "could not display user"})
