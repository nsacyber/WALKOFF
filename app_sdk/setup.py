from setuptools import setup, find_packages

setup(name='walkoff_app_sdk',
      version='0.1',
      description='WALKOFF App SDK',
      url='https://github.com/nsacyber/WALKOFF',
      author='WALKOFF Dev Team',
      author_email='',
      license='',
      packages=find_packages(),
      install_requires=["aiohttp", "pyyaml", "asteval", "cryptography", "six",
                        "tenacity", "python-socketio", "requests", "websocket-client"]
)
