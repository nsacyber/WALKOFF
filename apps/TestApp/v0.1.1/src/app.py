import asyncio
import time
import logging

from app_sdk.app_base import AppBase


class TestApp(AppBase):
    def __init__(self, redis=None, logger=None):
        super().__init__(redis, logger)

    def sleep(self, sleep_time=0):
        time.sleep(sleep_time)
        return time.time()

    def int_a_plus_b_minus_c(self, a, b, c):
        return a + b - c

    def int_a_times_int_b(self, a, b):
        return a * b

    def float_a_plus_b_minus_c(self, a, b, c):
        return a + b - c

    def float_a_time_float_b(self, a, b):
        return a * b

    def str_a_concat_with_str_b(self, a, b):
        return a + b

    def bool_a_and_bool_b(self, a, b):
        return a and b

    def add_key_val_to_dict(self, key, val, dictionary):
        dictionary[key] = val
        return dictionary

    def append_to_list(self, elem, list):
        list.append(elem)
        return list


def main(app_instance):
    import argparse
    LOG_LEVELS = ("debug", "info", "error", "warn", "fatal", "DEBUG", "INFO", "ERROR", "WARN", "FATAL")
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", dest="log_level", choices=LOG_LEVELS)
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="{asctime} - {name} - {levelname}:{message}", style='{')
    logger = logging.getLogger(f"TestApp{app_instance}")

    async def run():
        app = TestApp(logger=logger)
        async with app.connect_to_redis_pool() as redis:
            await app.get_actions()

    asyncio.run(run())


if __name__ == "__main__":
    main('')
