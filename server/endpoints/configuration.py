from datetime import timedelta

from flask import current_app
from flask_jwt_extended import jwt_required

import core.config.config
import core.config.paths
from server.returncodes import *
from server.security import roles_accepted_for_resources


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
            'clear_case_db_on_startup': bool(core.config.config.reinitialize_case_db_on_startup),
            'number_processes': int(core.config.config.num_processes),
            'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
            'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days)}


def read_config_values():

    @jwt_required
    @roles_accepted_for_resources('configuration')
    def __func():
        return __get_current_configuration(), SUCCESS
    return __func()


def update_configuration(configuration):
    from server.context import running_context
    from server.flaskserver import write_playbook_to_file

    @jwt_required
    @roles_accepted_for_resources('configuration')
    def __func():
        if 'workflows_path' in configuration:
            for playbook in running_context.controller.get_all_playbooks():
                try:
                    write_playbook_to_file(playbook)
                except (IOError, OSError):
                    current_app.logger.error('Could not commit old playbook {0} to file. '
                                             'Losing uncommitted changes!'.format(playbook))
            running_context.controller.load_playbooks()
        if not _reset_token_durations(access_token_duration=configuration.get('access_token_duration', None),
                                      refresh_token_duration=configuration.get('refresh_token_duration', None)):
            return {'error': 'Invalid token durations.'}, BAD_REQUEST

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
    return __func()


def _reset_token_durations(access_token_duration=None, refresh_token_duration=None):
    access_token_duration = (timedelta(minutes=access_token_duration) if access_token_duration is not None
                             else current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    refresh_token_duration = (timedelta(days=refresh_token_duration) if refresh_token_duration is not None
                              else current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])
    if access_token_duration < refresh_token_duration:
        current_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = access_token_duration
        current_app.config['JWT_REFRESH_TOKEN_EXPIRES'] = refresh_token_duration
        return True
    return False
