.. _index:

Welcome to WALKOFF's documentation!
===================================
Welcome to Walkoff’s Python documentation. If you are looking for documentation and tutorials on getting started with Walkoff, please first look at our Github Pages site. Here you’ll find tutorials and documentation on both UI usage and app and interface development. This documentation is intended to help app and interface developers as well as provide a reference for project contributors.


Deploying WALKOFF
------------------------
**Ensure that Python 3.7+, Docker, pip, and git are installed** 

1. Open a terminal on Linux or a command prompt on Windows, and run the command

.. code-block:: console

		git clone https://github.com/nsacyber/WALKOFF.git

2. Change directories to the WALKOFF directory

.. code-block:: console

		cd WALKOFF

3. Create an encryption key

.. code-block:: console

        python key_creation.py | docker secret create encryption_key -


3.  Perform the following commands to launch WALKOFF in stack mode

.. code-block:: console

		docker swarm init

Note: If you have multiple NICs you will need to use --advertise-addr to pick an address from which the swarm will be accessible.

.. code-block:: console

		docker-compose build


.. code-block:: console

		docker stack deploy --compose-file docker-compose.yml walkoff

4. Navigate to the default IP and port.

.. code-block:: console

		localhost:8080

the default IP and the port can be changed in the server. Configuration settings will be saved in the data/walkoff.config file.

5. Once navigated to the login page, the default username is "admin" and password is "admin." These can and should be changed upon initial login.

6. To shutdown WALKOFF, run the following two commands

.. code-block:: console
		
		docker stack rm walkoff

.. code-block:: console
		
		docker-compose down



.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

		Interface Overview <interface.rst>
		Workflow Development <workflow.rst>
		Prepackaged Applications <prepackaged_apps.rst>
		Application Development <apps.rst>
		API Gateway <api.rst>
        Changelog <changelog.rst>

