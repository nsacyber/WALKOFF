from setuptools import setup, find_packages
from codecs import open
from os import path
from walkoff import __version__ as version

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='walkoff',
    version=version,
    description='A flexible, easy to use, automation framework allowing users to integrate their capabilities'
                ' and devices to cut through the repetitive, tedious tasks slowing them down.',  # Required
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nsacyber/WALKOFF/',
    author='nsacyber',
    author_email='walkoff@nsa.gov',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Framework :: Flask',

        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',

        'Natural Language :: English',

        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',


        'Topic :: Home Automation',
        'Topic :: Security',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Monitoring',

        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: JavaScript',
    ],

    keywords='walkoff automation framework security cyber integration open source platform',

    packages=find_packages(exclude=['docs',
                                    'tests',
                                    'tests.*',
                                    'apps',
                                    'apps.*',
                                    'interfaces',
                                    'interfaces.*']),

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
                      'futures; python_version < "3"',
                      'semver',
                      'jsonschema',
                      'psutil>5.0.0',
                      'six>=1.10.0',
                      'diskcache>=3.0.1',
                      'marshmallow>=2.15,<3.0.0',
                      'marshmallow-sqlalchemy>=0.13.0',
                      'pynacl',
                      'alembic'
                      ],

    extras_require={
        'test': ['fakeredis >= 0.9.0',
                 'mock']
    },

    package_data={
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

    # data_files=[('my_data', ['data/data_file'])]

    entry_points={
        'console_scripts': [
            'walkoff-setup=walkoff.setup_walkoff:main',
            'walkoff-run=walkoff.__main__:main',
            'walkoff-update=walkoff.update_walkoff:main',
            'walkoff-install-deps=walkoff.scripts.install_dependencies:main',
            'walkoff-install-pkg=walkoff.scripts.install_package:main'
        ],
    },
)
