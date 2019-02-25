Walkoff Platform
================

{{ generate_module_autodocs('walkoff') }}


Workflow Executor
-----------------
This package contains classes used to execute workflows on both the server and the workers.

{{ generate_module_autodocs('walkoff.multiprocessedexecutor') }}

Execution Database
------------------
This package contains the SQLAlchemy tables used to define the workflows and related objects as well as the Marshmallow
schemas for the workflows.

{{ generate_module_autodocs('walkoff.executiondb') }}

App Gateway
-----------
This package provides the interface between the platform and the apps including providing the mechanisms to cache the
apps and actions, create app instances, and validate app api schemas and inputs to actions.

{{ generate_module_autodocs('walkoff.appgateway') }}

Cases
-----
This package supports the case logger

{{ generate_module_autodocs('walkoff.case') }}

Messaging
---------
This package provides methods to receive user messages from the workers and handle them appropriately.

{{ generate_module_autodocs('walkoff.messaging') }}

Server
------
This package contains functions and classes used by the server

{{ generate_module_autodocs('walkoff.server') }}

Server Blueprints
~~~~~~~~~~~~~~~~~
This package contains the Flask Blueprints used by the server for the root, interfaces, and SSE streams.

{{ generate_module_autodocs('walkoff.server.blueprints') }}

Server Endpoints
~~~~~~~~~~~~~~~~
This package contains the functions which define the endpoints for the REST API. The OpenAPI definitions in walkoff/api
contain information about which endpoint is connected to which function.

{{ generate_module_autodocs('walkoff.server.endpoints') }}


Server Database
---------------
This module contains the SqlAlchemy table definitions used by the server for tasks such as authentication and messaging.

{{ generate_module_autodocs('walkoff.serverdb') }}

