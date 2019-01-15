import logging

import yaml

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WALKOFF")

try:
    with open("data/config.yaml") as fp:
        config: dict = yaml.load(fp)

    redis_keys = {"action_result_ch": "action-results", "in_process_q": "actions-in-process",
                  "apigateway2umpire_ch": "api-gateway-umpire", "umpire2apigateway_ch": "umpire2api-gateway"}

    config["redis"].update(redis_keys)

except FileNotFoundError:
    logger.error("Config file not found.")
    config = {}
