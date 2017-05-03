import json
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context, current_user, write_playbook_to_file
from server import forms
import core.config.config
import core.config.paths


configurations_page = Blueprint('settings_page', __name__)


@configurations_page.route('/<string:key>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def config_values(key):
    if current_user.is_authenticated and key:
        if hasattr(core.config.paths, key):
            return json.dumps({str(key): str(getattr(core.config.paths, key))})
        elif hasattr(core.config.config, key):
            return json.dumps({str(key): str(getattr(core.config.config, key))})
        else:
            return json.dumps({str(key): "Error: key not found"})
    else:
        return json.dumps({str(key): "Error: user is not authenticated or key is empty"})


@configurations_page.route('/set', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/configuration'])
def set_configuration():
    if current_user.is_authenticated:
        form = forms.SettingsForm(request.form)
        if form.validate():
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
            return json.dumps({"status": 'success'})
        else:
            return json.dumps({"status": 'error: invalid form'})
    else:
        return json.dumps({"status": 'error: user is not authenticated'})
