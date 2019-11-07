import logging

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db.mongo import get_mongo_c
from api.server.db.settings import SettingsModel
from common import async_mongo_helpers as mongo_helpers

logger = logging.getLogger("API")
router = APIRouter()

@router.get("/",
            response_model=SettingsModel, response_description="Current settings in WALKOFF.")
async def read_settings(*, settings_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns the current settings in WALKOFF.
    """
    settings = await mongo_helpers.get_all_items(settings_col, SettingsModel)
    return settings[0]


@router.put("/",
            response_model=SettingsModel, response_description="The newly updated Settings.")
async def update_settings(*, settings_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         new_settings: SettingsModel):
    """
    Updates the Timeout settings for WALKOFF.
    This includes the JWT Access Token Duration (in minutes) and the JWT Refresh Token Duration (in days).
    """
    settings = await mongo_helpers.get_all_items(settings_col, SettingsModel)
    settings_id = settings[0].id_
    return await mongo_helpers.update_item(settings_col, SettingsModel, settings_id, new_settings)


# def update_settings():
#     config_in = request.get_json()
#     if not _reset_token_durations(access_token_duration=config_in.get('access_token_duration', None),
#                                   refresh_token_duration=config_in.get('refresh_token_duration', None)):
#         return Problem.from_crud_resource(
#             HTTPStatus.BAD_REQUEST,
#             'settings',
#             'update',
#             'Access token duration must be less than refresh token duration.')
#
#     for config, config_value in config_in.items():
#         if hasattr(api_gateway.flask_config.FlaskConfig, config.upper()):
#             setattr(api_gateway.flask_config.FlaskConfig, config.upper(), config_value)
#         elif hasattr(current_app.config, config.upper()):
#             setattr(current_app.config, config.upper(), config_value)
#
#     current_app.logger.info('Changed settings')
#     # TODO: Common config branch needs to reimplement this
#     # try:
#     #     api_gateway.config.Config.write_values_to_file()
#     #     return __get_current_settings(), HTTPStatus.OK
#     # except (IOError, OSError) as e:
#     #     current_app.logger.error('Could not write changes to settings to file')
#     #     return Problem(
#     #         HTTPStatus.INTERNAL_SERVER_ERROR,
#     #         'Could not write changes to file.',
#     #         f"Could not write settings changes to file. Problem: {format_exception_message(e)}")
#
#
# def _reset_token_durations(access_token_duration=None, refresh_token_duration=None):
#     access_token_duration = (timedelta(minutes=access_token_duration) if access_token_duration is not None
#                              else current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
#     refresh_token_duration = (timedelta(days=refresh_token_duration) if refresh_token_duration is not None
#                               else current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])
#     if access_token_duration < refresh_token_duration:
#         current_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = access_token_duration
#         current_app.config['JWT_REFRESH_TOKEN_EXPIRES'] = refresh_token_duration
#         return True
#     return False
