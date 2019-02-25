import os
import shutil
import sys

sys.path.append(os.path.abspath('.'))

import api_gateway.config


def generate_certificates():
    keys_dir = api_gateway.config.Config.KEYS_PATH

    # Create dirs for certs, remove old content if necessary
    if os.path.exists(keys_dir):
        shutil.rmtree(keys_dir)
    os.mkdir(keys_dir)


    # # Move public keys to appropriate dir
    # for key_file in os.listdir(keys_dir):
    #     if key_file.endswith(".key"):
    #         shutil.move(os.path.join(keys_dir, key_file), os.path.join(public_keys_dir, '.'))
    #
    # # Move secret keys to appropriate dir
    # for key_file in os.listdir(keys_dir):
    #     if key_file.endswith(".key_secret"):
    #         shutil.move(os.path.join(keys_dir, key_file), os.path.join(secret_keys_dir, '.'))


if __name__ == '__main__':
    generate_certificates()
