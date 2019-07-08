import api_gateway.flask_config
from api_gateway.helpers import compose_api

compose_api(api_gateway.flask_config.Config)


