from datetime import timedelta

from flask import current_app, request
from flask_jwt_extended import jwt_required

import walkoff.config
from walkoff.helpers import format_exception_message
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.problem import Problem
from walkoff.server.returncodes import *


def __get_current_configuration():
    return {'db_path': walkoff.config.Config.DB_PATH,
            'logging_config_path': walkoff.config.Config.LOGGING_CONFIG_PATH,
            'host': walkoff.config.Config.HOST,
            'port': int(walkoff.config.Config.PORT),
            'walkoff_db_type': walkoff.config.Config.WALKOFF_DB_TYPE,
            'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
            'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days),
            'zmq_results_address': walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
            'zmq_communication_address': walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS,
            'number_processes': int(walkoff.config.Config.NUMBER_PROCESSES),
            'number_threads_per_process': int(walkoff.config.Config.NUMBER_THREADS_PER_PROCESS),
            'cache': walkoff.config.Config.CACHE}


def read_config_values():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('configuration', ['read']))
    def __func():
        return __get_current_configuration(), SUCCESS

    return __func()


def update_configuration():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('configuration', ['update']))
    def __func():
        config_in = request.get_json()
        if not _reset_token_durations(access_token_duration=config_in.get('access_token_duration', None),
                                      refresh_token_duration=config_in.get('refresh_token_duration', None)):
            return Problem.from_crud_resource(
                BAD_REQUEST,
                'configuration',
                'update',
                'Access token duration must be less than refresh token duration.')

        for config, config_value in config_in.items():
            if hasattr(walkoff.config.Config, config.upper()):
                setattr(walkoff.config.Config, config.upper(), config_value)
            elif hasattr(current_app.config, config.upper()):
                setattr(current_app.config, config.upper(), config_value)

        current_app.logger.info('Changed configuration')
        try:
            walkoff.config.Config.write_values_to_file()
            return __get_current_configuration(), SUCCESS
        except (IOError, OSError) as e:
            current_app.logger.error('Could not write changes to configuration to file')
            return Problem(
                IO_ERROR,
                'Could not write changes to file.',
                'Could not write configuration changes to file. Problem: {}'.format(format_exception_message(e)))

    return __func()


def patch_configuration():
    return update_configuration()


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
