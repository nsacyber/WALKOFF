import api_gateway.config
from api_gateway.helpers import compose_api

compose_api(api_gateway.config.Config)


