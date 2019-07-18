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

#. Open a terminal on Linux or a command prompt on Windows, and clone WALKOFF:

    .. code-block:: console

            git clone https://github.com/nsacyber/WALKOFF.git

#. Change directories to the WALKOFF directory:

    .. code-block:: console

            cd WALKOFF


#.  Perform the following command to create a Docker Swarm with your host as the manager:

        .. code-block:: console

                docker swarm init

        **Note:** If you have multiple NICs you will need to use --advertise-addr to pick an address from which the swarm will be accessible.

#. Build WALKOFF's bootloader:

    .. code-block:: console

            ./build_bootloader.sh

#. Launch WALKOFF with the bootloader, building components as well:

    .. code-block:: console
    
    	    ./walkoff.sh up --build

#. Navigate to the default IP and port. The default IP and the port can be changed by altering the port NGINX is exposed on (the right-hand port) in the top-level `docker-compose.yml`.


    .. code-block:: console

            https://127.0.0.1:8080

#. Once navigated to the login page, the default username is "admin" and password is "admin." These can and should be changed upon initial login.


#. To shutdown WALKOFF, use the bootloader:

    .. code-block:: console

            ./walkoff.sh down



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

