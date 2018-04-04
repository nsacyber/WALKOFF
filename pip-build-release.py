import subprocess
import tarfile
import zipfile
import argparse
import os
import shutil


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

    if args.build:
        gzip_filename = "walkoff/walkoff_external.tar.gz"
        zip_filename = "walkoff/walkoff_external.zip"

        if os.path.exists(gzip_filename):
            os.remove(gzip_filename)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

        if args.clear:
            if os.path.exists("build/"):
                shutil.rmtree("build/")
            if os.path.exists("dist/"):
                shutil.rmtree("dist/")
            if os.path.exists("walkoff.egg-info/"):
                shutil.rmtree("walkoff.egg-info/")

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
