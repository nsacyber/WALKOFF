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

Pre-requisites
------------------------
**Ensure that Docker, Docker Compose 3+, and git are installed!**

* Docker CE: https://docs.docker.com/install/#supported-platforms
* Docker Compose: https://docs.docker.com/compose/install/
* Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

If you do not already have a Docker Swarm initialized or joined, run the following command to create one:

    .. code-block:: console

       docker swarm init

    **Note:** If you have multiple NICs you will need to use --advertise-addr to pick an address from which the swarm will be accessible.

Deploying WALKOFF in a Unix environment
---------------------------------------

#. Open a terminal and clone WALKOFF:

    .. code-block:: console

       git clone https://github.com/nsacyber/WALKOFF.git

#. Move into the WALKOFF directory:

    .. code-block:: console

       cd WALKOFF

#. Build WALKOFF's bootloader container, which handles management of the WALKOFF stack:

   * Creating Docker secrets, configs, networks, volumes, etc.
   * Building and pushing component images to WALKOFF's internal registry.
   * Deploying and removing the Docker Stack.

    .. code-block:: console

       ./build_bootloader.sh

#. Launch WALKOFF with the bootloader, building components as well:

    .. code-block:: console
    
       ./walkoff.sh up --build

       # If verbose output is desired:
       ./walkoff.sh up --build --debug

#. Navigate to the default IP and port. The default IP and the port can be changed by altering the port NGINX is exposed on (the right-hand port) in the top-level `docker-compose.yml`. Note that you should use HTTPS, and allow the self-signed certificate when prompted.

    .. code-block:: console

       https://127.0.0.1:8080

#. The default username is "admin" and password is "admin." These can and should be changed upon initial login.


#. To stop WALKOFF, use the bootloader:

    .. code-block:: console

       ./walkoff.sh down

       # If removing encryption key (and persistent data), stored images, and verbose output is desired:
       ./walkoff.sh down --key --registry --debug


Deploying WALKOFF in a Windows environment
------------------------------------------

#. Open PowerShell and clone WALKOFF:

    .. code-block:: console

       git clone https://github.com/nsacyber/WALKOFF.git

#. Move into the WALKOFF directory:

    .. code-block:: console

       cd WALKOFF

#. Use the provided `walkoff.ps1` script to initialize Walkoff's required components:

    .. code-block:: console

       # Create Docker volumes, secrets
       .\walkoff.ps1 init

       # Build and Push WALKOFF component images
       .\walkoff.ps1 build

#. Launch WALKOFF with `walkoff.ps1`:

    .. code-block:: console

       # Deploy WALKOFF stack
       .\walkoff.ps1 up

       # Check WALKOFF stack services
       .\walkoff.ps1 status

#. Navigate to the default IP and port. The default IP and the port can be changed by altering the port NGINX is exposed on (the right-hand port) in the top-level `docker-compose.yml`. Note that you should use HTTPS, and allow the self-signed certificate when prompted.

    .. code-block:: console

       https://127.0.0.1:8080

#. The default username is "admin" and password is "admin." These can and should be changed upon initial login.


#. To stop WALKOFF, use the bootloader:

    .. code-block:: console


       .\walkoff.ps1 stop

       # If removing encryption key, persistent data, stored images is desired:
       .\walkoff.ps1 down




|br|

.. toctree::
   :maxdepth: 2
   :caption: Contents:

		Home <self>
		Interface Overview <interface.rst>
		Walkoff Development <workflow.rst>
		Prepackaged Applications <prepackaged_apps.rst>
		Application Development <apps.rst>
		API Gateway <api.rst>
        Changelog <changelog.rst>

