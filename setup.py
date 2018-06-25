"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
from walkoff import __version__ as version

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='walkoff',  # Required
    version=version,  # Required
    description='A flexible, easy to use, automation framework allowing users to integrate their capabilities'
                ' and devices to cut through the repetitive, tedious tasks slowing them down.',  # Required

    url='https://github.com/nsacyber/WALKOFF/',  # Optional
    author='nsacyber',  # Optional
    author_email='walkoff@nsa.gov',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Topic :: Security',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Monitoring',

        # Pick your license as you wish
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords='walkoff automation framework security cyber integration open source platform',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(exclude=['docs',
                                    'tests',
                                    'tests.*',
                                    'apps',
                                    'apps.*',
                                    'interfaces',
                                    'interfaces.*']),  # Required

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['Flask>=0.10.0',
                      'Flask_SQLAlchemy==2.1',
                      'flask_jwt_extended>=3.4.0',
                      'sqlalchemy>=1.1.0',
                      'sqlalchemy-utils>=0.32.0',
                      'APscheduler>=3.0.0',
                      'gevent>=1.2',
                      'connexion>=1.1',
                      'pyyaml>=3.0',
                      'pyzmq>14.1.0',
                      'passlib>=1.7.0',
                      'blinker>=1.4',
                      'protobuf>= 3.4.0,<3.5.2',
                      'enum34',
                      'futures',
                      'semver',
                      'jsonschema',
                      'psutil>5.0.0',
                      'six>=1.10.0',
                      'diskcache>=3.0.1',
                      'marshmallow>=2.15,<3.0.0',
                      'marshmallow-sqlalchemy>=0.13.0',
                      'pynacl',
                      'alembic'
                      ],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    # extras_require={  # Optional
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    package_data={  # Optional
        'walkoff': ['client/assets/*',
                    'client/assets/img/*',
                    'client/dist/*',
                    'client/node_modules/bootstrap/dist/css/bootstrap.min.css',
                    'client/node_modules/bootstrap/dist/js/bootstrap.min.js',
                    'client/node_modules/jquery/dist/jquery.min.js',
                    'proto/data.proto',
                    'scripts/migrations/alembic.ini',
                    'scripts/migrations/database/*/README',
                    'scripts/migrations/database/*/*.mako',
                    'templates/*',
                    'walkoff_external.tar.gz',
                    'walkoff_external.zip']
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],  # Optional

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={  # Optional
        'console_scripts': [
            'walkoff-setup=walkoff.setup_walkoff:main',
            'walkoff-run=walkoff.__main__:main',
            'walkoff-update=walkoff.update_walkoff:main',
            'walkoff-install-deps=walkoff.scripts.install_dependencies:main',
            'walkoff-install-pkg=walkoff.scripts.install_package:main'
        ],
    },
)
