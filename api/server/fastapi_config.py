import logging

logger = logging.getLogger("API")


class FastApiConfig(object):
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'
    JWT_IDENTITY_CLAIM = 'identity'

    JWT_BLACKLIST_PRUNE_FREQUENCY = 1000
    MAX_STREAM_RESULTS_SIZE_KB = 156

    ALGORITHM = ["HS256"]
