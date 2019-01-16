import logging
import configparser
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WALKOFF")
CONFIG_PATH = (Path(__file__).parent / "../data/config.ini").resolve()


def load_config():
    try:
        # Load the user configurable parameters
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        # Append dev config options or overwrite config options the user shouldn't have set
        redis_keys = {"action_result_ch": "action-results", "in_process_q": "actions-in-process",
                      "apigateway2umpire_ch": "api-gateway-umpire", "umpire2apigateway_ch": "umpire2api-gateway"}
        config["REDIS"].update(redis_keys)

        return config

    except KeyError as e:
        logger.exception(f"Config section {e.args[0]} not found.")


if __name__ == "__main__":
    config = load_config()
    if config:
        print([key for key in config.keys()])