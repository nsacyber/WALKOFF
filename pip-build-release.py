import subprocess
import tarfile
import argparse


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--production",
                        help="Upload to pypi.org.",
                        action="store_true")
    parser.add_argument("-t", "--test",
                        help="Upload to test.pypi.org instead of production.",
                        action="store_true")
    parser.add_argument("-b", "--build",
                        help="Build only, don't upload.",
                        action="store_true")

    args = parser.parse_args()

    a = tarfile.open("walkoff/walkoff_external.tar.gz", "w|gz")
    a.add("walkoff_external/")
    a.close()

    subprocess.call(['python', 'setup.py', 'sdist'])
    subprocess.call(['python', 'setup.py', 'bdist_wheel', '--universal'])

    if not args.build and args.test:
        subprocess.call(['twine', 'upload', '--repository-url', 'https://test.pypi.org/legacy/', 'dist/*'])


if __name__ == '__main__':
    main()
