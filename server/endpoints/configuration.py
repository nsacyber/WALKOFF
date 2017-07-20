from flask import current_app
from flask_security import roles_accepted
import core.config.config
import core.config.paths
from server.return_codes import *


def __get_current_configuration():
    return {'workflows_path': core.config.paths.workflows_path,
            'templates_path': core.config.paths.templates_path,
            'db_path': core.config.paths.db_path,
            'case_db_path': core.config.paths.case_db_path,
            'log_config_path': core.config.paths.logging_config_path,
            'host': core.config.config.host,
            'port': int(core.config.config.port),
            'walkoff_db_type': core.config.config.walkoff_db_type,
            'case_db_type': core.config.config.case_db_type,
            'https': bool(core.config.config.https),
            'tls_version': core.config.config.tls_version,
            'clear_case_db_on_startup': bool(core.config.config.reinitialize_case_db_on_startup)}


def read_config_values():
    from server.context import running_context
    from server.flaskserver import current_user

    @roles_accepted(*running_context.user_roles['/configuration'])
    def __func():
        if current_user.is_authenticated:
            return __get_current_configuration(), SUCCESS
        else:
            current_app.logger.warning('Configuration attempted to be grabbed by '
                                       'non-authenticated user')
            return {"error": 'User is not authenticated.'}, UNAUTHORIZED_ERROR
    return __func()


def update_configuration(configuration):
    from server.context import running_context
    from server.flaskserver import current_user, write_playbook_to_file

    @roles_accepted(*running_context.user_roles['/configuration'])
    def __func():
        if current_user.is_authenticated:
            if 'workflows_path' in configuration:
                for playbook in running_context.controller.get_all_playbooks():
                    try:
                        write_playbook_to_file(playbook)
                    except (IOError, OSError):
                        current_app.logger.error('Could not commit old playbook {0} to file. '
                                                 'Losing uncommitted changes!'.format(playbook))
                running_context.controller.load_all_workflows_from_directory()
            for config, config_value in configuration.items():
                if hasattr(core.config.paths, config):
                    setattr(core.config.paths, config, config_value)
                elif hasattr(core.config.config, config):
                    setattr(core.config.config, config, config_value)
            current_app.logger.info('Changed configuration')
            try:
                core.config.config.write_values_to_file()
                return __get_current_configuration(), SUCCESS
            except (IOError, OSError):
                current_app.logger.error('Could not write changes to configuration to file')
                return {"error": 'Could not write to file.'}, IO_ERROR
        else:
            current_app.logger.warning('Configuration attempted to be set by non authenticated user')
            return {"error": 'User is not authenticated.'}, UNAUTHORIZED_ERROR
    return __func()
