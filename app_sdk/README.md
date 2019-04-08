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

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should make a call to super().__init__ to set up Redis and logging.
        """
        super().__init__(redis, logger, console_logger)
    
    # Define all desired functions as asyncio couroutines using the "async" keyword
    async def hello_world(self):
        """
        A simple action to return hello world!
        """
        message = f"Hello World!"

        # This logs to the docker or local log
        self.logger.info(message)

        # This sends a log message to the frontend
        await self.console_logger.info(message)
        
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
