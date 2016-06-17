#Installs SetupTools if none
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "WALKOFF",
    version = "0.0.5",
    packages = find_packages(),

    install_requires = ['blinker >= 1.4',
                        'Flask >= 0.10.0',
                        'Flask_Login >= 0.3.2',
                        'Flask_Principal >= 0.4.0',
                        'Flask_SQLAlchemy >= 2.1',
                        'Flask_Security >= 1.7.5',
                        'Flask_WTF >= 0.12',
                        'jinja2 >= 2.8',
                        'sqlalchemy >= 1.0.12',
                        'wtforms >= 2.1',
                        'werkzeug >= 0.11.4',
                        'requests >= 2.9.1',
                        'importlib'],

    # metadata for upload to PyPI
    description = "This package is a reference implementation of the WALKOFF development standard.",
    license = "Apache",
    keywords = "orchestration cybersecurity automation",
    url = "http://github.com/iadgov/walkoff",
    zip_safe = False,
    classifiers = [
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)

