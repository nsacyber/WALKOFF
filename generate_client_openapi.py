from pathlib import Path
import yaml

from common.config import static
from api_gateway.helpers import compose_api

compose_api(static)

with open(Path(static.API_PATH) / "composed_api.yaml") as f:
    y = yaml.full_load(f)

for path, methods in y['paths'].items():
    for method, config in methods.items():
        if method not in ('get', 'post', 'put', 'patch', 'delete'):
            continue

        config['operationId'] = config['operationId'].split(".")[-1]

for name, schema in y['components']['schemas'].items():
    schema.pop('additionalProperties', None)

with open(Path(static.API_PATH) / "client_api.yaml", 'w') as f:
    yaml.dump(y, f, width=float("inf"))
