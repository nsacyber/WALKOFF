.. _index:
.. |br| raw:: html

   <br />

Welcome to WALKOFF's documentation!
===================================
This documentation is intended as a reference for app and workflow developers as well as project contributors and operators.
Here you will find walkthroughs, tutorials and other useful information about applications that are shipped with Walkoff, our changelog, and how to interact with Walkoff using its RESTful API.

What is WALKOFF?
------------------
WALKOFF is a flexible, easy to use, automation framework allowing users to integrate their capabilities and devices to cut through the repetitive, tedious tasks slowing them down,

**WHAT WE OFFER**
    * *Easy-to-use:* Drag-and-drop workflow editor. Sharable apps and workflows.
    * *Flexbility:* Deployable on Windows or Linux.
    * *Modular:* Plug and play integration of almost anything with easy-to-develop applications.
    * *Visual Analytics:* Send workflow data to custom dashboards (and soon, Elasticsearch & Kibana!)

.. _deploying-walkoff-label:

Deploying WALKOFF
------------------------
**Ensure that Docker, Docker-Compose 3+, and git are installed**

#. Open a terminal on Linux or a command prompt on Windows, and clone the Walkoff project.

    .. code-block:: console

            git clone https://github.com/nsacyber/WALKOFF.git

#. Change directories to the WALKOFF directory

    .. code-block:: console

            cd WALKOFF


#.  Perform the following command to launch WALKOFF in swarm mode

        .. code-block:: console

                docker swarm init

        **Note:** If you have multiple NICs you will need to use --advertise-addr to pick an address from which the swarm will be accessible.

#. Create an encryption key

    .. code-block:: console

            docker run --rm python:3.7-alpine python -c "import os; print(os.urandom(16).hex())" | docker secret create encryption_key -

#. Create data/registry directory

    .. code-block:: console
    
    	    mkdir data/registry

#.  Perform the following command to launch WALKOFF with stack mode

        .. code-block:: console

                docker-compose build
                docker stack deploy --compose-file docker-compose.yml walkoff

#. Navigate to the default IP and port. The default IP and the port can be changed in the server. Configuration settings will be saved in the ``common/config.py`` file. Walkoff now uses HTTPS by default through NGINX.


    .. code-block:: console

            https://localhost:8080

#. Once navigated to the login page, the default username is "admin" and password is "admin." These can and should be changed upon initial login.


#. To shutdown WALKOFF, run the following two commands. The first command may not remove all services; as the Umpire container exits, it will try to clean up the rest. Run the command again after a few seconds; if it does not fully clean up, you will have to manually remove services.

    .. code-block:: console

            docker stack rm walkoff
            # Some seconds later
            docker stack rm walkoff



|br|

.. toctree::
   :maxdepth: 2
   :caption: Contents:

		Home <self>
		Interface Overview <interface.rst>
		Workflow Development <workflow.rst>
		Prepackaged Applications <prepackaged_apps.rst>
		Application Development <apps.rst>
		API Gateway <api.rst>
        Changelog <changelog.rst>

