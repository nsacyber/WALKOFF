# Changelog
<!-- Use the tags Added, Changed, Deprecated, Removed, Fixed, Security, and
     Contributor to describe changes -->

## [0.8.0]
###### 2018-04-16

### Added
* Multiple tools have been added to help develop workflows
  * Playbooks can be saved even if they are invalid. However, playbooks cannot
    be executed if they are invalid.
  * The playbook editor displays the errors on a workflow which must be solved
    before the workflow can be executed
  * You can now use Python's builtin `logging` module in an app, and the log
    messages will be displayed in the playbook editor
* The metrics page has been introduced in the UI which displays simple metrics
  related to the execution of workflows and actions.
* The devices used in the actions in workflows are now objects, enabling
  dynamic selection of the device used for the action. To further support this,
  an action in the Utilities app named `get devices by fields` allows you to
  query the devices database.
* The ability to use a key-value storage has been created. This is now the
  mechanism used to push workflows and backs the SSE streams. Currently two
  options are available for key-value store, DiskCache, a SQLite-backed
  key-value storage, and Redis. By default Walkoff will use DiskCache, but it
  is recommended that users configure and use Redis.
* The SSEs now use dedicated SseStream objects which are backed by the cache.
  These objects make constructing and using streams much easier.
  `walkoff.see.InterfaceSseStream` and `walkoff.sse.FilteredInterfaceSseStream`
  objects have been made available to use in custom interfaces.
* A `CaseLogger` object which makes it much easier to log events to the case
  database has been created.

### Changed
* The `interfaces.AppBlueprint` used to construct interfaces has been modified
  to extend from `walkoff.sse.StreamableBlueprint` which in turn extends
  Flask's Blueprint. This makes the interface cleaner and more flexible.
* Changes to the REST API
  * In the configuration resource:
    * `workflow_path`, `logging_config_file`, and `zmq_requests` have been
      removed from the API
    * The ability to edit the cache configuration has been added
  * In the playbook resources:
    * All execution elements have a read only list of human-readable errors
    * A workflow has a read only Boolean field "is_valid" which indicates if
      any of its execution elements have errors
* All changes to the configuration will only be applied on server restart
* Refactorings have been done to minimize the amount of global state used
  throughout Walkoff. Work will continue on this effort.
* Metrics are now stored in the execution database
* Changes to styling on the playbook editor


### Deprecated
* `walkoff.helpers.create_sse_event` has been deprecated and will be removed in
  version 0.10.0. Use `walkoff.sse.SseEvent` or the streams in `walkoff.sse`
  instead
  .
### Fixed
* Bug where branches where all branches weren't being evaluated in a workflow
* Bug where object arguments could not be converted from strings

### Contributor
* Testing the backend now requires the additional the dependencies in
  `requirements-test.txt`
* The minimum accepted unit test coverage for the Python backend is now 88%

## [0.7.4]
###### 2018-03-20

### Fixed
* Bug where some device fields were being deleted on update

## [0.7.3]
###### 2018-03-14

### Fixed
* Bug where NO_CONTENT return codes were failing on Werkzeug WSGI 0.14

### Changed
* All node modules are now bundled into webpack


## [0.7.2]
###### 2018-03-12

### Fixed
* An unintentional backward-breaking change was made to the format of the
  dictionary used in the interface dispatcher which sometimes resulted in
  a dict with a "data" field inside a "data" field. This has been fixed.


## [0.7.1]
###### 2018-03-08

### Changed
* Improved deserialization in the user interface
* Empty arrays are omitted from returned execution element JSON structure in
  the REST API.

### Fixed
* `PATCH /api/devices` now doesn't validate that all the fields of the device
  are provided.
* Fixed dependency bug on GoogleProtocolBuffer version


## [0.7.0]
###### 2018-03-07
### Added
* An execution control page is now available on the user interface. This page
  allows you to start, pause, resume, and abort workflows as well as displays
  the status of all running and pending workflows.
  * With this feature is a new resource named `workflowqueue` which is
    available through the `/api/workflowqueue` endpoints.
* You now have the ability to use a full set of Boolean logic on conditions.
  This means that on branches and triggers you can specify a list of conditions
  which must all be true (AND operator), or a list of conditions of which any
  must be true (OR operator), or a list of conditions of which exactly one must
  be true (XOR operator). You can also negate conditions or have child
  conditions. This new conditional structure is called a ConditionalExpression
  and wraps the old Condition objects.
* Playbooks can be exported to and imported from a JSON text file using the new
  `GET /api/playbooks?mode=export` and the `POST /api/playbooks` using a
  `multipart/form-data` body respectively.

### Changed
* Significant changes to the REST API
  * We have changed the HTTP verbs used for the REST API to reflect their more
    widely-accepted RESTful usage. Specifically, the POST and PUT verbs have
    been swapped for most of the endpoints.
  * Workflows are now accessed through the new `/api/workflows` endpoints
    rather than the `/api/playbooks` endpoints
  * The `/api/playbooks` and the `/api/workflows` endpoints now use the UUID
    instead of the name.
  * The `/api/playbook/{id}/copy` and the
    `/api/playbooks/{id}/workflows/{id}/copy` endpoints are now accessed
    through `POST /api/playbooks?source={id_to_copy}` and the
    `POST /api/workflows?source={id_to_copy}` endpoints respectively.
  * Server-Sent Event streams are now located in the `/api/streams` endpoints
  * Errors are now returned using the RFC 7807 Problem Details standard
* Playbooks, workflows, and their associated execution elements are now stored
  in the database which formerly only held the devices. The both greatly
  increased scalability as well as simplified the interactions between the
  server and the worker processes as well as increased scalability.
* Paused workflows and workflows awaiting trigger data are now pickled
  (serialized to binary) and stored in a database table. Before, a conditional
  wait -was used to pause the execution of a workflow. By storing the state to
  the database, all threads on all worker processes are free to execute
  workflows.
* Information about the workflow which sent events are now available in both
  the Google Protocol Buffer messages as well as the arguments to callbacks
  using the interface event dispatcher.
* All times are stored in UTC time and represented in RFC 3339 format
* The marshmallow object serialization library is now used to serialize and
  deserialize execution elements instead of our old homemade solution

### Deprecated
* The "sender_uids" argument in the interface dispatcher `on_xyz_event`
  decorators is now an alias for "sender_ids". **This will be removed in
  version 0.9.0**

### Removed
* The `/api/playbooks/{name}/workflows/{name}/save` endpoint has been removed.
* The `/api/playbooks/{name}/workflows/{name}/{execute/pause/resume}` endpoints
  have been removed. Use the `/api/workflowqueue` resource instead
* Removed `workflow_version` from the playbooks. This may be added later to
  provide backwards-compatible import functionality to the workflows.
* `/api/devices/import` and `/api/devices/export` endpoints have been
removed. Use the new `POST /api/devices` with `multipart/form-data` and
`GET /api/devices?mode=export` endpoints respectively.


### Contributor
* The minimum accepted unit test coverage for the Python backend is now 86%


## [0.6.7]
###### 2018-02-06

### Fixed
* Fixed bug in `create_sse_event` where data field of the SSE would not be
  populated if no data was not specified, causing the SSE event to be invalid

## [0.6.6]
###### 2018-02-02

### Changed
* Omitting `sender_uids` or `names` on `dispatcher.on_xyz_event` decorators
  in interfaces now registers the decorated function for all senders. This
  is consistent with the previously inaccurate code examples in the tutorials.

## [0.6.5]
###### 2018-02-02

### Added
* Webpack is now used to increase UI performance

### Changed
* Default return codes for the Walkoff app

### Contributor
* Some UI tests are now run on Travis-CI


## [0.6.4]
###### 2018-01-18

### Changed
* The accept/decline method returns status codes indicating if the action was
  accepted or declined instead of true/false


### Fixed
* Fixed a bug where roles weren't being deleted from the database
* Fixed issue preventing permissions to be removed on editing roles
* Fixed issue with messages not properly being marked as responded

## [0.6.3]
###### 2018-01-18

### Added
* Added a simple action in the Utilities app named "request user approval"
  which sends a message with some text to a user and has an accept/decline
  component.

### Changed
* Refactoring of AppCache to use multiple objects. We had been storing it as
  a large dict which was becoming difficult to reason about. This is the
  first step of a larger planned refactoring of how apps are cached and
  validated

### Fixed
* Bug on UI when arguments using an array type without item types specified
* Fixed issue with workflow migration caused to erroneously deleting a script


## [0.6.2]
###### 2018-01-05

Multithreaded workers for increased asynchronous workflow execution

### Added
* Multiple workflows can be executed on each worker process
* Decorator factory to simplify endpoint logic
* Endpoint to get system stats

### Fixed
* Bug where roles couldn't be assigned to a user on creation

### Contributor
* Added AppVeyor to test Walkoff on Windows

## [0.6.1]
###### 2018-01-03


### Added
* Multiple workflows can be executed on each worker process

### Changed
* Bumped dependency of `flask-jwt-extended` to version 3.4.0

### Fixed
* Default logging config issue
* Removed `walkoff/client/build` which was accidentally version controlled
* CodeClimate misconfiguration
* Bug fixes to messaging caused by messaging callback not being registered in
  the server

## [0.6.0]
###### 2018-01-03

Introducing roles, messages, and notifications

### Added
* Administrators can now create custom roles and assign users to those roles.
  Each resource of the server endpoint is protected by a permission, and roles
  can be created which combine resource permissions.
* Messages and notifications
  * Actions can now send messages to users
  * Messages can be used to convey information to users or to pause a workflow
    and wait for a user to approve its continued execution
  * When a user receives a message, a notification will appear
* Easy updates
  * An update script is provided to update to the most recent version if one is
    available. This script includes custom workflow migration scripts and
    database migration scripts generated by SqlAlchemy-Alembic. These are a work in progress.
      * _Note 1: Database migrations only work for default database locations and
        using SQLite. This can be changed in the `alembic.ini` file_
      * _Note 2: Now that databases and workflows can be updated
        easily, minor version updates will not occur on backward-breaking
        changes to the database schema or the playbook schema._
  * This script also includes utility functions for backing up the WALKOFF directory, cleaning pycache, setting up WALKOFF after an update, etc.
* Explicit failure return codes for actions
  * Return codes which indicate a failure of the action can be marked with
    `failure: true`. This will cause an ActionExecutionError event to be sent
* Explicit success default return codes for actions
  * The default return code for an action can be specified with
    `default_return: YourReturnHere`
* Internal ZeroMQ addresses can be configured through the UI
* Added this change log

### Changed
* Significant repository restructure
  * This repository restructure combined the `core` and `server` packages into
    a single `walkoff` package and moved modules such as `appcache` and
    `devicedb` out of the `apps` package
  * Top-level scripts with the exception of `walkoff.py` are now located in the
    `scripts` directory
  * These changes make the Walkoff project follow a more canonical repository
    structure, and are one step towards being able to install walkoff using
    `pip`, our eventual goal.
* Classes have been moved out of the `server.context.Context` class. They were
  located there to remove circular dependencies, but they have been moved into
  their own submodule.
* The `interface.__init__` module has been split into multiple modules
* The Sphinx Python documentation has been relocated to the `docs` directory
  and can be generated using `make html`. Additionally, they now use the
  ReadTheDocs theme.
* Google Protocol Buffer message structure has been significantly altered.
* Tags used for action, condition, and transform decorators have been
  encapsulated in a WalkoffTag enum
* `setup_walkoff.py` no longer explicitly calls Gulp

### Security
* JWT structure changes
  * JWTs' identity is now the user ID, not the username
  * JWT claims are now the username and a list of role IDs this user
    possesses. These claims are populated on login, and require
    reauthentication to be updated.

## [0.5.2]
###### 2017-12-20

### Fixed
* Fixed a bug where the config host and port were not initialized before
  the server started.

## [0.5.1]
###### 2017-12-14

### Fixed
* A bug fix for case management due to a typo in the TS.

## [0.5.0]
###### 2017-11-29

Introducing a more user-friendly playbook editor and custom event-driven
interfaces

### Added
* New user-friendly playbook editor
* Host and port can now be specified on the command line
* App-specific conditions and transforms
  * Conditions and transforms are now located in apps rather than in core, so
    they can be more easily created
* Branches now contain a "priority" field which can be used to determine the
  order in which the branches of a given action are evaluated
* Arguments to actions, conditions, and transforms which use references can
  select which component of the referenced action's output to use.
* Migration scripts to help ease a variety of backward-breaking changes --
  `migrate_workflows.py` and `migrate_api.py`
* Scripts to create Sphinx documentation have been added to the repository


### Changed
* Custom interfaces with event handling
  * Interfaces are no longer attached to apps; they are now their own plugins
    and are contained in the `interfaces` directory
  * Interfaces can use new decorator functions to listen and respond to all
    events in Walkoff as they occur
* Better triggers
  * Triggers are no longer specified in the database. Instead, each individual
    action in a workflow can have its own set of conditions which can act as
    breakpoints in a workflow. You can send data to them through the server and
    have that data validated against a set of conditions before the action can
    resume.
  * You can still start a workflow from the beginning through the server
* Renamed workflow components for clarity
  * "steps" have been renamed "actions"
  * "next steps" have been renamed "branches"
  * "flags" have been renamed "conditions"
  * "filters" have been renamed "transforms"
* Script used to start the server has been renamed `walkoff.py`
* ZeroMQ keys are contained in the `.certificates` directory
* Playbook file format changes
  * Branches are now contained outside of actions, creating two top-level
    fields.
  * Branches have a `source_uid` and a `destination_uid` instead of just a
    `name` field
  * The `start` step on a workflow is indicated with the start step's UID
    instead of its name
  * The `app` and `action` fields of actions, conditions, and transforms have
    been renamed `app_name` and `action_name` respectively.
  * Conditions and transforms contain an `app_name` field instead of just an
    `action` field
  * We have removed the `widgets` field and the `risk` field from actions
  * Devices for actions are specified by id rather than by name
  * Actions' `inputs` field, as well as conditions' and transforms' `args`
    field has been renamed `arguments` and is now a complete JSON object
  * Playbooks now contain a `walkoff_version` field which will be used to
    indicate which version of WALKOFF created them. This will be helpful in the
    future to migrate workflows to new formats
* Minor changes to api.yaml schema
  * `dataIn` has been renamed `data_in`
  * `termsOfService` has been renamed `terms_of_service`
  * `externalDocs` has been renamed `external_docs` and is always an array
* Performance of worker processes has been improved by removing gevent from
  child processes and reducing polling
* The blinker Signals used to trigger events have been wrapped in a
  WalkoffEvent enum
* Internal sockets used for ZeroMQ communication have been moved to
  `core.config.config`
* Actions which are defined inside of a class must supply a device, or the
  workflow will fail on initialization
* The REST API to get the APIs of apps has been enhanced significantly and
  returns all of the API


### Removed
* Unfortunately, event-driven actions have been broken for some time now. We
  have removed this functionality, but are working on an even better
  replacement for them in the meantime
* We have removed accumulated risk from workflows and risk from steps. This
  feature will be re-added at a future date
* We have removed widgets from the backend. This feature will be reimplemented
  later.
* Backend support for adding roles to users has been removed. All users are
  administrators as they have been in previous releases. There was never a UI
  component for this feature, and it was breaking some other components for
  editing users. Roles will be re-added in the next release.

### Security
* HTTPS is enabled by default if certificates are placed in the
  `.certificates` directory.

### Contributor
* Coverage.py is used to generate test coverage report. Travis-CI will fail if
  the code coverage is below 81% This percentage will rise over time


## [0.4.2]
###### 2017-11-09

### Fixed
* Bug fixes to Playbook editor
* Bug in global action execution

## [0.4.1]
###### 2017-11-03

### Fixed
* Bug fixes to playbook editor

## [0.4.0]
###### 2017-10-30

Introducing custom devices and global app actions

### Added
* Custom devices
  * Apps define their own fields needed in their devices
* Global app actions
  * Actions no longer need to be defined in a class

### Fixed
* Performance improvements and bug fixes

## [0.3.1]
###### 2017-09-25

### Fixed
* Bug Fixes

## [0.3.0]
###### 2017-09-15

Introducing a new Angular-driven UI, schedulers, cases, and concurrency

### Added
* Brand new UI 
* Better concurrent execution of CPU-bound workflows
* Multiple workflows can be executed on the same scheduler
* New Scheduler UI page
* New Case Management UI

### Changed
* Improved REST API
* Workflows are now stored as JSON

### Fixed
* Bugs and performance improvements

### Security
* Enhanced security using JSON Web Tokens
* Workflows are stored as JSON

## [0.2.1]
###### 2017-07-14

### Added
* Event-driven app actions
* Multiple return codes for actions and error handling

### Changed
* Apps are now located in Walkoff-Apps repo
* Workflow results are stored in case database

### Fixed
* Bug fixes and performance improvements

## [0.2.0]
###### 2017-06-21

Introducing app action validation and improved data flow

### Added
* New app specification using YAML metadata files
    * Better input validation using JSON schema
    * Arguments can be string, integer, number, arrays, or JSON objects
* Workflow animation during execution in the workflow editor
* Results from previously executed actions can be used later in workflows
* Better workflow monitoring during execution
* New apps
    * NMap
    * Splunk
    * TP-Link 100 Smart Outlet

### Fixed
* UI styling and bug fixes
* Bug fixes and performance improvements

## [0.1.2]
###### 2017-05-25

### Added
* New Lifx playbook

### Fixed
* Bug fixes to UI and apps


## [0.1.1]
###### 2017-05-25

### Added

* OpenAPI Specification for server endpoints and connexion Flask app
* New Apps
    * AR.Drone
    * Ethereum Blockchain
    * Facebook User Post
    * Webcam
    * Watson Visual Recognition
    * Tesla
    * Lifx
* Better error handling in server endpoints
* Bug fixes
* Swagger UI documentation

### Changed
* UI improvements


## [0.1.0]
###### 2017-05-15

Initial Release

