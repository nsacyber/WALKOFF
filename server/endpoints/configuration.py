from flask import request, current_app
from flask_security import roles_accepted
from server import forms
import core.config.config
import core.config.paths
from server.return_codes import *


def read_config_values(key):
    from server.context import running_context
    from server.flaskserver import current_user

    @roles_accepted(*running_context.user_roles['/configuration'])
    def __func():
        if current_user.is_authenticated and key:
            if hasattr(core.config.paths, key):
                return {str(key): str(getattr(core.config.paths, key))}
            elif hasattr(core.config.config, key):
                return {str(key): str(getattr(core.config.config, key))}, SUCCESS
            else:
                current_app.logger.warning('Configuration key {0} not found. Cannot get key.'.format(key))
                return {str(key): "Error: key not found"}, OBJECT_DNE_ERROR
        else:
            current_app.logger.warning(
                'Configuration attempted to be grabbed by non authenticated user or key was empty')
            return {str(key): "Error: user is not authenticated or key is empty"}, OBJECT_DNE_ERROR
    return __func()


def update_configuration():
    from server.context import running_context
    from server.flaskserver import current_user, write_playbook_to_file

    @roles_accepted(*running_context.user_roles['/configuration'])
    def __func():
        if current_user.is_authenticated:
            form = forms.SettingsForm(request.form)
            for key, value in form.data.items():
                if hasattr(core.config.paths, key):
                    if key == 'workflows_path' and key != core.config.paths.workflows_path:
                        for playbook in running_context.controller.get_all_playbooks():
                            try:
                                write_playbook_to_file(playbook)
                            except (IOError, OSError):
                                pass
                        core.config.paths.workflows_path = value
                        running_context.controller.workflows = {}
                        running_context.controller.load_all_workflows_from_directory()
                    else:
                        setattr(core.config.paths, key, value)
                        if key == 'apps_path':
                            core.config.config.load_function_info()
                else:
                    setattr(core.config.config, key, value)
            current_app.logger.info('Changed configuration')
            return {"status": 'success'}, SUCCESS
        else:
            current_app.logger.warning('Configuration attempted to be set by non authenticated user')
            return {"status": 'error: user is not authenticated'}
    return __func()
