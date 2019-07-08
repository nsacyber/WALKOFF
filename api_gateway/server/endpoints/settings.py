from datetime import timedelta

from flask import current_app, request
from flask_jwt_extended import jwt_required

import api_gateway.flask_config
from api_gateway.helpers import format_exception_message
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import Problem
from http import HTTPStatus


def __get_current_settings():
    return {'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
            'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days)}


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('settings', ['read']))
def read_settings():
    return __get_current_settings(), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('settings', ['update']))
def update_settings():
    config_in = request.get_json()
    if not _reset_token_durations(access_token_duration=config_in.get('access_token_duration', None),
                                  refresh_token_duration=config_in.get('refresh_token_duration', None)):
        return Problem.from_crud_resource(
            HTTPStatus.BAD_REQUEST,
            'settings',
            'update',
            'Access token duration must be less than refresh token duration.')

    for config, config_value in config_in.items():
        if hasattr(api_gateway.flask_config.FlaskConfig, config.upper()):
            setattr(api_gateway.flask_config.FlaskConfig, config.upper(), config_value)
        elif hasattr(current_app.config, config.upper()):
            setattr(current_app.config, config.upper(), config_value)

    current_app.logger.info('Changed settings')
    # try:
    #     api_gateway.config.Config.write_values_to_file()
    #     return __get_current_settings(), HTTPStatus.OK
    # except (IOError, OSError) as e:
    #     current_app.logger.error('Could not write changes to settings to file')
    #     return Problem(
    #         HTTPStatus.INTERNAL_SERVER_ERROR,
    #         'Could not write changes to file.',
    #         f"Could not write settings changes to file. Problem: {format_exception_message(e)}")


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
