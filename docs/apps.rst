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
If you would like to follow along by adding a VirusTotal app to your Walkoff instance, follow the **EXAMPLE** bullets at the end of most steps.

**1. Write Python Functions in a Standalone Script**
    * Start by developing your app and its functions in a standalone script outside of WALKOFF – this way you can get basic functionality down before dealing with WALKOFF.
    * **Note:** all functions that you expect to turn into actions must be written asynchronously (i.e. ``async def function_name()``)
    * **EXAMPLE:** Below is example code that can be used to interact with VirusTotal's Api as a standalone script
 
 	.. code-block:: python
	
	    def _pretty_print(some_dict):
        	pretty = json.dumps(some_dict, sort_keys=False, indent=4)
        	print(pretty)
        	return pretty

	    async def ip_lookup(self, ip, apikey):
		url = 'https://www.virustotal.com/vtapi/v2/ip-address/report'
		parameters = {'ip': ip, 'apikey': apikey}
		response = requests.get(url, params=parameters)
		response_dict = response.json()
		pretty = self._pretty_print(response_dict)
		await self.console_logger.info(pretty)
		return pretty

**2. Copy the hello_world application folder from the WALKOFF/apps directory**
    * Rename the copied package to the name of your desired application
    *  **Note:** The package name must be in ``snake_case`` and should have the same name as the app you want to create. 
    * **EXAMPLE:** Make sure you are in the WALKOFF/apps directory before continuing with example below.
    
    	.. code-block:: console
	
		cp -r hello_world virus_total
    
**3. Copy your developed python functions into the** ``app.py`` **file in the** ``1.0.0/src`` **directory**
    * Ensure that your new functions are included *under* the HelloWorld class declaration. 
    * **Note:** Only files under ``src`` will be copied into the application's Docker container.
    * **EXAMPLE:** Delete everything after ``def __init__()`` but before ``if __name__ == "__main__",`` then paste your standalone script into the gap that has been cleared for your code. One line above the pretty print script, add ``@staticmethod`` to the same column start as ``def _pretty_print``. This is because ``_pretty_print`` is a *helper function* and we won't define it in the api.yaml later on.

**4. Change the HelloWorld class name in** ``app.py`` **to match the class name of your new app**
    * Ensure that this class name matches the asyncio ``__main__`` call at the bottom of ``app.py``
    * Likewise, also change the app_name value to reflect your new application name
    * **EXAMPLE:** For this step we will change the name of the HelloWorld class to VirusTotal, then below that, change the "app_name" value to be "virus_total" instead of "hello_world". Finally at the end of the file change HelloWorld.run() to be VirusTotal.run(). By the end of all of these actions, your app.py file should look like this: 
    
    .. image:: ../docs/images/vt.png
    
**5. Change the** ``api.yaml`` **metadata file to describe your app and its actions**
    * For WALKOFF to recognize a function as an action, it must have a corresponding entry in the app's ``api.yaml`` file
    * The action names in this file must exactly match your function names in code.
    * You must include at least ``name``, ``app_version``, and ``actions`` in this file.
    * **EXAMPLE:** 
    	.. code-block:: html
	
		walkoff_version: 1.0.0
		app_version: 1.0.0
		name: virus_total
		description: Send api call to Virus Total for various actions.
		contact_info:
		  name: Walkoff Team
		  url: https://github.com/nsacyber/walkoff
		  email: walkoff@nsa.gov
		license_info:
		  name: Creative Commons
		  url: https://github.com/nsacyber/WALKOFF/blob/master/LICENSE.md
		actions:
		  - name: ip_lookup
		    description: Look up an IP in VT database
		    parameters:
		      - name: apikey
			schema:
			  type: string
			required: true
			description: enter api key
		      - name: ip
			schema:
			  type: string
			required: true
			description: enter ip address
		    returns:
		      schema:
			type: string

**6. Change the** ``requirements.txt`` **to match your applications needs**
    * This file should include any Python package dependencies your app contains
    * The Dockerfile will use this to pip install dependencies
    * **EXAMPLE:** 
    	.. code-block:: python
		
		requests

**7. Change the** ``docker-compose`` **YAML file**
    * This will control how your app’s Docker container will run.
    * At a minimum, utilize the ``hello_world`` application's ``docker-compose.yml`` and simply change the service name to match that of your new application.
        * **Note:** If you want directories on your host to be available in the container, you can add volume mounts here.
    * **EXAMPLE:**
    
	    .. code-block:: html
	    
		version: '3.4'
		services:
		  virus_total:
		    build:
		      context: .
		      dockerfile: Dockerfile
		#    image: walkoff_registry:5000/walkoff_app_HelloWorld-v1-0
		    env_file:
		      - env.txt
		    deploy:
		      mode: replicated
		      replicas: 10
		      restart_policy:
			condition: none
		      placement:
			constraints: [node.role==manager]
		    restart: "no"

**Optional:** ``Dockerfile`` **Customization**
    * This will control how your app will be built.
    * See ``hello_world’s Dockerfile`` for a detailed, step-by-step example on how to create your own ``Dockerfile``
    * If your application's Python dependencies require any OS libraries to build, or if your application requires any OS packages to run, include them in this file.
    * You can test building your app with the Dockerfile before running it in WALKOFF:

        .. code-block:: console

                docker build -f apps/app_name/1.0.0/Dockerfile apps/app_name/1.0.0
    * **EXAMPLE:** We won't be doing anything here.

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



