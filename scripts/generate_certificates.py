import os
import shutil
import sys

import zmq.auth

sys.path.append(os.path.abspath('.'))

import walkoff.config


def generate_certificates():
    keys_dir = walkoff.config.Config.KEYS_PATH
    public_keys_dir = walkoff.config.Config.ZMQ_PUBLIC_KEYS_PATH
    secret_keys_dir = walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH

    # Create dirs for certs, remove old content if necessary
    for d in [keys_dir, public_keys_dir, secret_keys_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.mkdir(d)

    # Create new keys in certs dir
    zmq.auth.create_certificates(keys_dir, "server")
    zmq.auth.create_certificates(keys_dir, "client")

    # Move public keys to appropriate dir
    for key_file in os.listdir(keys_dir):
        if key_file.endswith(".key"):
            shutil.move(os.path.join(keys_dir, key_file), os.path.join(public_keys_dir, '.'))

    # Move secret keys to appropriate dir
    for key_file in os.listdir(keys_dir):
        if key_file.endswith(".key_secret"):
            shutil.move(os.path.join(keys_dir, key_file), os.path.join(secret_keys_dir, '.'))


if __name__ == '__main__':
    generate_certificates()
