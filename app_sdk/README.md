## WALKOFF App SDK

WALKOFF 1.0 includes an SDK to ease the development of WALKOFF apps. This is still in development and will likely change 
in the coming days.

## Installation
The SDK is pip installable using the following commands:

```
# Clone this repo & branch:
git clone -b 1.0.0-alpha.1 https://github.com/nsacyber/WALKOFF.git

# Navigate to where the docker-compose.yml is:
cd WALKOFF/app_sdk

# Install the app SDK as an editable pip package for easy updates
pip install -e .
```

## Minimalistic App Example
```
import asyncio

# Import the application base from the sdk
from walkoff_app_sdk.app_base import AppBase


class HelloWorld(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console logging set up behind the scenes.
    """
    __version__ = "1.0.0"

    def __init__(self, redis, logger):
        """
        Each app should make a call to super().__init__ to set up Redis and logging.
        """
        super().__init__(redis, logger)
    
    # Define all desired functions as asyncio couroutines using the "async" keyword
    async def hello_world(self):
        """
        A simple action to return hello world!
        """
        message = f"Hello World!"

        # This logs to the docker or local log
        self.logger.info(message)
        
        # Returns the message as an action result to the frontend
        return message


# The entrypoint for each app should look like this
if __name__ == "__main__":
    asyncio.run(HelloWorld.run())
```
For a more complete example of a WALKOFF application, please refer to the `hello_world` skeleton application in the 
`WALKOFF/apps` directory. 
Please note, the minimal directory structure for an application is as follows:
```
WALKOFF
+-- apps
     +-- app_name 
          +-- version_number
               |-- Dockerfile
               |-- docker-compose.yml
               |-- api.yml
               +-- src
                    +-- your_code.{c, cpp, py,..., etc.} 
```

## Testing an app outside of WALKOFF 

Running an app on its own outside of WALKOFF can be useful for debugging, as the app service logs are somewhat buried.

Keep in mind while running your app this way, you will have access to your host's filesystem in a way that is not normally accessible to app containers. 

1. Install the WALKOFF App SDK (assuming you're starting from WALKOFF's directory):
   ```
   cd app_sdk
   pip install -e .
   ```

2. Run the rest of WALKOFF via docker-compose as described in the main Readme
   ```
   cd ..
   docker-compose up -d --build
   ```
3. Export environment variables that the app would normally expect inside its container, but change service names to localhost 
   ```
   export REDIS_URI=redis://localhost
   export REDIS_ACTION_RESULT_CH=action-results
   export REDIS_ACTION_RESULTS_GROUP=action-results-group
   export APP_NAME=hello_world
   export HOSTNAME=$(hostname)
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```
3. Navigate to and run your app.py. The app will exit after a set period if no work is found, so ensure you run your app just before the workflow.
   ```
   python apps/hello_world/1.0.0/src/app.py 
   ```
   
## Adding an app to WALKOFF

To "install" an app in WALKOFF, simply place your app with the above structure inside the apps directory. The Umpire will detect and build it on a set interval (default 60 seconds), adding it to the list of available. This process will change and be made more secure/robust as the 1.0 release matures.
