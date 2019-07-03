Welcome to WALKOFF's documentation!
===================================
This documentation is intended as a reference for app and workflow developers as well as project contributors and operators.
Here you will find walkthroughs, tutorials and other useful information about applications that are shipped with Walkoff, our changelog, and how to interact with Walkoff using its RESTful API.

What is WALKOFF?
------------------
WALKOFF is a flexible, easy to use, automation framework allowing users to integrate their capabilities and devices to cut through the repetitive, tedious tasks slowing them down,

**WHAT WE OFFER**
 - *Easy-to-use:* Drag-and-drop workflow editor. Sharable apps and workflows.
 - *Flexbility:* Deployable on Windows or Linux.
 - *Modular:* Plug and play integration of almost anything with easy-to-develop applications.
 - *Visual Analytics:* Send workflow data to custom dashboards (and soon, Elasticsearch & Kibana!)


Deploying WALKOFF
------------------------
**Ensure that Docker, Docker-Compose 3+, and git are installed**

1. Open a terminal on Linux or a command prompt on Windows, and clone the Walkoff project.

            git clone https://github.com/nsacyber/WALKOFF.git

2. Change directories to the WALKOFF directory

            cd WALKOFF


3.  Perform the following command to launch WALKOFF in swarm mode

                docker swarm init

       **Note:** If you have multiple NICs you will need to use --advertise-addr to pick an address from which the swarm will be accessible.

4. Create an encryption key

            docker run python:3.7-alpine python -c "import os; print(os.urandom(16).hex())" | docker secret create encryption_key -

5. Create data/registry directory
    
    	    mkdir data/registry

6.  Perform the following command to launch WALKOFF with stack mode

                docker-compose build
                docker stack deploy --compose-file docker-compose.yml walkoff

7. Navigate to the default IP and port. The default IP and the port can be changed in the server. Configuration settings will be saved in the ``common/config.py`` file. Walkoff now uses HTTPS by default through NGINX.

            https://localhost:8080

8. Once navigated to the login page, the default username is "admin" and password is "admin." These can and should be changed upon initial login.


9. To shutdown WALKOFF, run the following two commands. The first command may not remove all services; as the Umpire container exits, it will try to clean up the rest. Run the command again after a few seconds; if it does not fully clean up, you will have to manually remove services.

            docker stack rm walkoff
            # Some seconds later
            docker stack rm walkoff
