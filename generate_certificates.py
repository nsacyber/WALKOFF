import os
import shutil
import zmq.auth
import core.config.paths


def generate_certificates():
    keys_dir = core.config.paths.zmq_keys_path
    public_keys_dir = core.config.paths.zmq_public_keys_path
    secret_keys_dir = core.config.paths.zmq_private_keys_path

    # Create dirs for certs, remove old content if necessary
    for d in [keys_dir, public_keys_dir, secret_keys_dir]:
        print(d)
        if os.path.exists(d):
            shutil.rmtree(d)
        os.mkdir(d)

    # Create new keys in certs dir
    server_public_file, server_secret_file = zmq.auth.create_certificates(keys_dir, "server")
    client_public_file, client_secret_file = zmq.auth.create_certificates(keys_dir, "client")

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
