import os

import zipfile
import tarfile
import argparse


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
    cwd = os.getcwd()
    ls = os.listdir(cwd)
    if 'walkoff.py' not in ls:
        print("Did not detect 'walkoff.py' in this directory. Run this script from your WALKOFF root directory.\n\
        Example in WALKOFF directory: python scripts/install_package.py -a /path/to/my_package.tar.gz")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--archive",
                        help="Install WALKOFF package from tar.gz or zip archive.")
    # parser.add_argument("-u", "--url",
    #                     help="Install WALKOFF package from url of tar.gz or zip archive.")
    args = parser.parse_args()

    # if args.url is not None:
    #     filename = get_archive(args.url)
    # else:
    filename = args.archive

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
