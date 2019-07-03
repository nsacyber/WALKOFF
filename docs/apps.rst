.. _apps:

.. |br| raw:: html

   <br />

Application Development
========================

The minimal directory structure for a WALKOFF application is as follows:

.. code-block:: console

        WALKOFF
        +-- apps
             +-- app_name
                  +-- version_number
                       |-- Dockerfile
                       |-- docker-compose.yml
                       |-- api.yml
                       +-- src
                            +-- your_code.{c, cpp, py,..., etc.}
                            +-- any other files you wish to be accessible in the app container

Development Instructions
-------------------------
*For a complete example of a WALKOFF application, please refer to the hello_world skeleton application in the WALKOFF/apps directory.*

**1. Write Python Functions in a Standalone Script**
    * Start by developing your app and its functions in a standalone script outside of WALKOFF – this way you can get basic functionality down before dealing with WALKOFF.
    * **Note:** all functions that you expect to turn into actions must be written asynchronously (i.e. ``async def function_name()``)

**2. Create a Package in the Apps directory of WALKOFF**
    *  **Note:** The package name must be in ``snake_case`` and should have the same name as the app you want to create
    * Within the new application package, store all files within a version number folder (i.e. "1.0.0")
    * Place your developed app script into a ``src`` folder within the version folder.
    * Only files under ``src`` will be copied into the application's Docker container.

**3. Create an** ``api.yaml`` **metadata file to describe your app and its actions**
    * For WALKOFF to recognize a function as an action, it must have a corresponding entry in the apps's ``api.yaml`` file
    * Place this file at the same level as the ``src`` directory
    * Note:
        * The action names in this file must exactly match your function names in code.
        * You must include at least ``name``, ``app_version``, and ``actions`` in this file.

**4. Include a** ``requirements.txt``
    * This file should include any Python package dependencies your app contains
    * Place this file at the same level as the ``src`` directory
    * The Dockerfile will use this to pip install dependencies

**5. Create a** ``docker-compose`` **YAML file**
    * This will control how your app’s Docker container will run.
    * Place this file at the same level as the ``src`` directory
    * At a minimum, utilize the ``hello_world`` application's ``docker-compose.yml`` and simply change the service name to match that of your new application.
        * **Note:** If you want directories on your host to be available in the container, you can add volume mounts here.

**6. Create a** ``Dockerfile``
    * This will control how your app will be built.
    * See ``hello_world’s Dockerfile`` for a detailed, step-by-step example on how to create your own ``Dockerfile``
    * If your application's Python dependencies require any OS libraries to build, or if your application requires any OS packages to run, include them in this file.
    * You can test building your app with the Dockerfile before running it in WALKOFF:

        .. code-block:: console

                docker build -f apps/app_name/1.0.0/Dockerfile apps/app_name/1.0.0

Updating Your Application
''''''''''''''''''''''''''''
If your application Docker service is already running and you would like to update your app in WALKOFF, run these following commands with the proper substitions for application name ``hello_world``

.. code-block:: console

	app_dir=apps/hello_world/1.0.0
	app_tag=localhost:5000/walkoff_app_hello_world:1.0.0
	docker build -f $app_dir/Dockerfile -t $app_tag $app_dir
	docker push $app_tag
	docker service rm walkoff_app_hello_world

Naming and String Requirements:
'''''''''''''''''''''''''''''''''
    * App name must be ``snake_case`` and match in all the following locations:
        #. app directory
        #. app_name in ``app.py``
        #. app_name in ``api.yaml``
        #. service name in ``docker-compose.yml``
    * Your action names in ``api.yaml`` must match the function names they correspond to in ``app.py``
    * If your script is not named ``app.py``, the new name must match the command at the end of your ``Dockerfile``

|br|

Troubleshooting
----------------
There are several key places to look to debug an application:

#.  **Umpire**
    |br| Following the umpire’s logs (``docker service logs -f walkoff_umpire``) can give you an indication of whether build issues are happening within the stack. Building an app for the very first time can take a long time for example if it contains C dependencies that need to be compiled.

#.  **Docker Services**
    |br| Watching docker services (``watch -n 0.5 docker service ls``) can give you an indication of whether your app is running or crashing. At idle with no work, apps and workers will scale to 0/N replicas. If you see something repeatedly scaling up and back down to 0, it may be crashing.

#.  **Worker Service Logs**
    |br| Checking the worker service log after the service becomes available for the first time (``docker service logs -f worker``) will allow you to view the worker logs. Generally apps will not cause problems here, but there may be edge cases missing in scheduling apps.

#.  **App Service Logs**
    |br| Checking the app service log after the service becomes available for the first time (``docker service logs -f walkoff_app_app_name``) will allow you to view the stdout of your app, as well as any exceptions it might be raising.
    
#.  **Console Logging** 
    |br| If you are more familiar with print debugging, you can add information to the console logger by following the code below. This will display the console output in the workflow editor page under the tab ``Console``. 
    
     .. code-block:: console	
	
	message = "This is to be printed to the console logger"
	await self.console_logger.info(message)       
       
#.  **App Containers**

    * Obtain app_container_name from docker ps.
    * You can docker exec -it app_container_name /bin/sh into your app container while it is running to check things like network connectivity, the filesystem, or to run your app manually inside it. (If it is crashing on startup, you will need to fix that first or override its starting command with a sleep instead)

You can also run the app manually outside of docker entirely. Keep in mind while running your app this way, you will have access to your host's filesystem in a way that is not normally accessible to app containers.

    #. Install the WALKOFF App SDK (assuming you're starting from WALKOFF's directory)

        .. code-block:: console

                cd app_sdk
                pip install -e .

    #. Add debug flags to the umpire's service definition in ``docker-compose.yml``

        .. code-block:: yaml

                umpire:
                  command: python -m umpire.umpire --log-level=debug --disable-app-autoheal --disable-app-autoscale
                  image: localhost:5000/umpire:latest
                  build:
                   context: ./
                   dockerfile: umpire/Dockerfile
                  networks:
                   - walkoff_default
                <...>

    #. Run the rest of WALKOFF via docker-compose as described in the main Readme

        .. code-block:: console

                cd ..
                docker stack deploy --compose-file=docker-compose.yml walkoff

    #. Export environment variables that the app would normally expect inside its container, but change service names to localhost

        .. code-block:: console

                export REDIS_URI=redis://localhost
                export REDIS_ACTION_RESULT_CH=action-results
                export REDIS_ACTION_RESULTS_GROUP=action-results-group
                export APP_NAME=hello_world
                export HOSTNAME=$(hostname)
                export PYTHONPATH="${PYTHONPATH}:$(pwd)"

    #. Navigate to and run your app.py. The app will exit if no work is found, so ensure you run your app just after executing the workflow.

        .. code-block:: console

                python apps/hello_world/1.0.0/src/app.py



