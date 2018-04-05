import subprocess
import tarfile
import zipfile
import argparse
import os
import shutil
from six.moves import input
import sys
from distutils.util import strtobool


def zip_dir(path, zip_file, arcname=None):
    for root, dirs, files in os.walk(path):
        for f in files:
            new_root = root.replace(path, arcname)
            zip_file.write(os.path.join(root, f), arcname=os.path.join(new_root, f))


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--production",
                        help="Upload to pypi.org.",
                        action="store_true")
    parser.add_argument("-t", "--test",
                        help="Upload to test.pypi.org instead of production.",
                        action="store_true")
    parser.add_argument("-b", "--build",
                        help="Build",
                        action="store_true")
    parser.add_argument("-c", "--clear",
                        help="Clear build/ and dist/",
                        action="store_true")

    args = parser.parse_args()

    gzip_filename = "walkoff/walkoff_external.tar.gz"
    zip_filename = "walkoff/walkoff_external.zip"

    if args.clear:
        if os.path.exists("build/"):
            shutil.rmtree("build/")
        if os.path.exists("dist/"):
            shutil.rmtree("dist/")
        if os.path.exists("walkoff.egg-info/"):
            shutil.rmtree("walkoff.egg-info/")

        if os.path.exists(gzip_filename):
            os.remove(gzip_filename)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

        if os.path.exists("README.rst"):
            os.remove("README.rst")

    if args.build:

        try:
            import pypandoc
        except ImportError:
            print("Run `pip install pypandoc`. This is required to generate a README.rst from our README.md for pypi.")
            return

        try:
            pypandoc.convert_file('README.md', 'rst', outputfile="README.rst")
        except OSError:
            print("Pandoc executable not found. Install Pandoc: https://pandoc.org/installing.html")
            print("Can also attempt to install Pandoc automatically, y/n?")

            while True:
                try:
                    s = input()
                    if strtobool(s.lower()):
                        from pypandoc.pandoc_download import download_pandoc
                        download_pandoc()
                        pypandoc.convert_file('README.md', 'rst', outputfile="README.rst")
                except ValueError:
                    print("Please respond with 'yes' or 'no'.")

        t = tarfile.open(gzip_filename, "w|gz")
        t.add("apps/", arcname="walkoff_external/apps/")
        t.add("interfaces/", arcname="walkoff_external/interfaces/")
        t.add("data/", arcname="walkoff_external/data/")
        t.close()

        z = zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED)
        zip_dir("apps/", z, arcname="walkoff_external/apps/")
        zip_dir("interfaces/", z, arcname="walkoff_external/interfaces/")
        zip_dir("data/", z, arcname="walkoff_external/data/")
        z.close()

        subprocess.call(['python', 'setup.py', 'sdist'])
        subprocess.call(['python', 'setup.py', 'bdist_wheel', '--universal'])

    if args.test:
        subprocess.call(['twine', 'upload', '--repository-url', 'https://test.pypi.org/legacy/', 'dist/*'])


if __name__ == '__main__':
    main()
