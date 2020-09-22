Join us for a WALKOFF community virtual event on September 23rd! 
---------------------------------------------------------------------------------
https://www.eventbrite.com/e/walkoff-consortium-automating-at-the-speed-of-operations-registration-118693482401

Check out the WALKOFF community subreddit! 
--------------------------------------------------------------------------------
https://www.reddit.com/r/walkoffcommunity/


Welcome to WALKOFF's documentation!
===================================
This documentation is intended as a reference for app and workflow developers as well as project contributors and operators.
Here you will find walkthroughs, tutorials and other useful information about applications that are shipped with Walkoff, our changelog, and how to interact with Walkoff using its RESTful API.

What is WALKOFF?
------------------
WALKOFF is a flexible, easy to use, automation framework allowing users to integrate their capabilities and devices to cut through the repetitive, tedious tasks slowing them down,

**WHAT WE OFFER**
 - *Easy-to-use:* Drag-and-drop workflow editor. Sharable apps and workflows.
 - *Flexibility:* Deployable on Windows or Linux.
 - *Modular:* Plug and play integration of almost anything with easy-to-develop applications.
 - *Visual Analytics:* Send workflow data to custom dashboards (and soon, Elasticsearch & Kibana!)

Documentation
------------------------
https://walkoff.readthedocs.io/en/latest/

Pre-requisites
------------------------
**Ensure that Docker, Docker Compose 3+, and git are installed!**

* Docker CE: https://docs.docker.com/install/#supported-platforms
* Docker Compose: https://docs.docker.com/compose/install/
* Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

If you do not already have a Docker Swarm initialized or joined, run the following command to create one:

    docker swarm init

**Note:** If you have multiple NICs you will need to use --advertise-addr to pick an address from which the swarm will be accessible.

Deploying WALKOFF in a Unix environment
---------------------------------------

1. Open a terminal and clone WALKOFF:

       git clone https://github.com/nsacyber/WALKOFF.git

2. Move into the WALKOFF directory:

       cd WALKOFF

3. Build WALKOFF's bootloader container, which handles management of the WALKOFF stack:
   
       ./build_bootloader.sh
       
   The bootloader performs the following tasks: 
   * Creating Docker secrets, configs, networks, volumes, etc.
   * Building and pushing component images to WALKOFF's internal registry.
   * Deploying and removing the Docker Stack.
   
4. Launch WALKOFF with the bootloader, building components as well:

       ./walkoff.sh up --build

       # If verbose output is desired:
       ./walkoff.sh up --build --debug

5. Navigate to the default IP and port. The default IP and the port can be changed by altering the port NGINX is exposed on (the right-hand port) in the top-level `docker-compose.yml`. Note that you should use HTTPS, and allow the self-signed certificate when prompted.

       https://127.0.0.1:8080

6. The default username is "admin" and password is "admin." These can and should be changed upon initial login.

7. To stop WALKOFF, use the bootloader:

       ./walkoff.sh down

       # If removing encryption key (and persistent data), stored images, and verbose output is desired:
       ./walkoff.sh down --key --registry --debug


Deploying WALKOFF in a Windows environment
------------------------------------------

1. Open PowerShell and clone WALKOFF:

       git clone https://github.com/nsacyber/WALKOFF.git

2. Move into the WALKOFF directory:

       cd WALKOFF

3. Use the provided `walkoff.ps1` script to initialize Walkoff's required components:

       # Create Docker volumes, secrets
       .\walkoff.ps1 init

       # Build and Push WALKOFF component images
       .\walkoff.ps1 build

4. Launch WALKOFF with `walkoff.ps1`:

       # Deploy WALKOFF stack
       .\walkoff.ps1 up

       # Check WALKOFF stack services
       .\walkoff.ps1 status

5. Navigate to the default IP and port. The default IP and the port can be changed by altering the port NGINX is exposed on (the right-hand port) in the top-level `docker-compose.yml`. Note that you should use HTTPS, and allow the self-signed certificate when prompted.

       https://127.0.0.1:8080

6. The default username is "admin" and password is "admin." These can and should be changed upon initial login.

7. To stop WALKOFF, use the bootloader:

       .\walkoff.ps1 stop

       # If removing encryption key, persistent data, stored images is desired:
       .\walkoff.ps1 down


