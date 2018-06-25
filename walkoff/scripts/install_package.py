import os

import zipfile
import tarfile
import argparse

from walkoff import config


def safe_unzip(zip_file, extract_path):
    with zipfile.ZipFile(zip_file, 'r') as zf:
        for member in zf.infolist():
            abspath = os.path.abspath(os.path.join(extract_path, member.filename))
            if abspath.startswith(os.path.abspath(extract_path)):
                zf.extract(member, extract_path)
            else:
                raise ValueError("Attempted to extract file with path outside the specified path, aborting.")


def safe_untar(tar_file, compression, extract_path):
    with tarfile.open(tar_file, 'r'+compression) as tf:
        for member in tf.getmembers():
            abspath = os.path.abspath(os.path.join(extract_path, member.name))
            if abspath.startswith(os.path.abspath(extract_path)):
                tf.extract(member, path=extract_path)
            else:
                raise ValueError("Attempted to extract file with path outside the specified path, aborting.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--archive",
                        help="Install WALKOFF package from tar.gz or zip archive.")
    parser.add_argument('-c', '--config', help='configuration file to use')
    # parser.add_argument("-u", "--url",
    #                     help="Install WALKOFF package from url of tar.gz or zip archive.")
    args = parser.parse_args()
    config_path = args.config if args.config is not None else os.getcwd()
    if os.path.isdir(config_path):
        config_path = os.path.join(config_path, "data", "walkoff.config")
    config.Config.load_config(config_path)

    # if args.url is not None:
    #     filename = get_archive(args.url)
    # else:

    filename = args.archive

    if not os.path.isfile(filename):
        print("{} does not exist, exiting.")
        return

    if filename.endswith("tar.gz"):
        safe_untar(filename, ':gz', '.')
    elif filename.endswith("tar.bz2"):
        safe_untar(filename, ':bz2', '.')
    elif filename.endswith("tar"):
        safe_untar(filename, '', '.')
    elif filename.endswith("zip"):
        safe_unzip(filename, '.')
    else:
        raise ValueError("File extension not supported.'")


if __name__ == "__main__":
    main()
