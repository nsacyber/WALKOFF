from flask import request, current_app
from flask_security import roles_accepted
from server import forms

def get_roles():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        roles = running_context.Role.query.all()
        if roles:
            result = [role.name for role in roles]
            return result
        else:
            current_app.logger.error('Cannot display roles. No roles exist.')
            return {"status": "roles do not exist"}
    return __func()

def create_role(role_name):
    from server.context import running_context
    from server.flaskserver import default_urls
    from server.database import add_to_user_roles
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        form = forms.NewRoleForm(request.form)
        if form.validate():
            if not running_context.Role.query.filter_by(name=role_name).first():

                if form.description.data is not None:
                    description = form.description.data
                    running_context.user_datastore.create_role(name=role_name, description=description,
                                                               pages=default_urls)
                else:
                    description = ''
                    running_context.user_datastore.create_role(name=role_name, pages=default_urls)

                add_to_user_roles(role_name, default_urls)

                running_context.db.session.commit()
                current_app.logger.info('Role added: {0}'.format({"name": role_name,
                                                                             "description": description,
                                                                             "urls": default_urls}))
                return {"status": "role added " + role_name}
            else:
                current_app.logger.warning('Cannot add role {0}. Role already exists'.format(role_name))
                return {"status": "role exists"}
    return __func()

def read_role(role_name):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        role = running_context.Role.query.filter_by(name=role_name).first()
        if role:
            return role.display()
        else:
            current_app.logger.error('Cannot display role {0}. Role does not exist.'.format(role_name))
            return {"status": "role does not exist"}
    return __func()

def update_role(role_name):
    from server.context import running_context
    from server.database import add_to_user_roles
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        role = running_context.Role.query.filter_by(name=role_name).first()
        if role:
            form = forms.EditRoleForm(request.form)
            if form.validate():
                if form.description.data:
                    role.set_description(form.description.data)
                if form.pages.data:
                    add_to_user_roles(role_name, form.pages)
            current_app.logger.info('Edited role {0} to {1}'.format(role_name,
                                                                    {"name": role_name,
                                                                                "description": form.description.data,
                                                                                "urls": form.pages.data}))
            return role.display()
        else:
            current_app.logger.error('Cannot edit role {0}. Role does not exist.'.format(role_name))
            return {"status": "role does not exist"}
    return __func()
