from datetime import timedelta

from flask import current_app
from flask_jwt_extended import jwt_required

import walkoff.config.config
import walkoff.config.paths
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions


def __get_current_configuration():
    return {'workflows_path': walkoff.config.paths.workflows_path,
            'db_path': walkoff.config.paths.db_path,
            'case_db_path': walkoff.config.paths.case_db_path,
            'log_config_path': walkoff.config.paths.logging_config_path,
            'host': walkoff.config.config.host,
            'port': int(walkoff.config.config.port),
            'walkoff_db_type': walkoff.config.config.walkoff_db_type,
            'case_db_type': walkoff.config.config.case_db_type,
            'clear_case_db_on_startup': bool(walkoff.config.config.reinitialize_case_db_on_startup),
            'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
            'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days),
            'zmq_requests_address': walkoff.config.config.zmq_requests_address,
            'zmq_results_address': walkoff.config.config.zmq_results_address,
            'zmq_communication_address': walkoff.config.config.zmq_communication_address,
            'number_processes': int(walkoff.config.config.num_processes),
            'number_threads_per_process': int(walkoff.config.config.num_threads_per_process)}


def read_config_values():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('configuration', ['read']))
    def __func():
        return __get_current_configuration(), SUCCESS

    return __func()


def update_configuration(configuration):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('configuration', ['update']))
    def __func():
        if not _reset_token_durations(access_token_duration=configuration.get('access_token_duration', None),
                                      refresh_token_duration=configuration.get('refresh_token_duration', None)):
            return {'error': 'Invalid token durations.'}, BAD_REQUEST

        for config, config_value in configuration.items():
            if hasattr(walkoff.config.paths, config):
                setattr(walkoff.config.paths, config, config_value)
            elif hasattr(walkoff.config.config, config):
                setattr(walkoff.config.config, config, config_value)

        current_app.logger.info('Changed configuration')
        try:
            walkoff.config.config.write_values_to_file()
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
