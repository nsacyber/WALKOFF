[![Build Status](https://img.shields.io/travis/nsacyber/WALKOFF/master.svg?maxAge=3600&label=Linux)](https://travis-ci.org/nsacyber/WALKOFF) [![Build status](https://ci.appveyor.com/api/projects/status/hs6ujwd1f87n39ut/branch/master?svg=true)](https://ci.appveyor.com/project/iadgovuser11/walkoff/branch/master)
[![Maintainability](https://api.codeclimate.com/v1/badges/330249e13845a07a69a2/maintainability)](https://codeclimate.com/github/iadgov/WALKOFF/maintainability)[![GitHub (pre-)release](https://img.shields.io/github/release/nsacyber/WALKOFF/all.svg?style=flat)](release)


<img src="https://nsacyber.github.io/WALKOFF/files/images/flyingLogoWithTextSmall.png">

# Description

* Are repetitive, tedious processes taking up too much of your time?
* Is more time spent focusing on managing your data than acting on the data
  itself?

WALKOFF is an automation framework that allows you to easily automate these 80%
of tedious tasks so you can get the job done faster, easier, and cheaper.

WALKOFF is built upon an app based architecture which enables the plug and play
integration of devices and capabilities.  These capabilities can then be tied
together to form Workflows.  Workflows are defined in a JSON format making them
easily sharable across environments and organizations and easily
created/customizable through our drag and drop workflow editor.

<center><img src="https://raw.githubusercontent.com/nsacyber/WALKOFF/gh-pages/files/images/demoGIFs/DragDropGIF.gif" height=300></center>

WALKOFF also makes it easier to manage your newly automated processes with
real-time visual updates and feeds based on your workflows progress.

<img src="https://raw.githubusercontent.com/nsacyber/WALKOFF/gh-pages/files/images/demoGIFs/realTimeUpdates.gif" height=300>

Apps can also have custom interfaces enabling app developers to uniquely
display information.  WALKOFF not only makes it easier for users to automate
their processes but allows users to act on their processes faster as well.

<img src="https://raw.githubusercontent.com/nsacyber/WALKOFF/gh-pages/files/images/demoGIFs/customAnalytics.gif" height=300>

Walkoff apps can be found at: <https://github.com/nsacyber/WALKOFF-Apps>

## Base Requirements

* Python 2.7+ or Python 3.4+
* NodeJS v4+ and Node Package Manager (npm) v5+
    * On Ubuntu, if you install `node` via `apt-get`, it will be installed as `nodejs` - you may need to create a symlink from your installed `nodejs` to `node` for `npm` to work correctly.
    * npm v5 requires Node v4+, while npm v6 requires Node v6+. Using [NVM (Node Version Manager)](https://github.com/creationix/nvm) can assist in obtaining the correct versions of NodeJS and NPM.
* Redis 5+
    * Redis can be run on Linux (see https://redis.io/topics/quickstart or check your OS's package manager), 
    * If you are using Windows, you will need to use Redis in a VM or a Docker container.
* Best used with Linux, or in Docker
    * On Linux, you will need the `python-devel` package for your distribution if running natively.

*Individual apps may specify their own requirements.*

## Installation Instructions

### Docker

Please see the Readme on Docker Cloud for instructions on running WALKOFF in a docker container: https://cloud.docker.com/repository/docker/walkoffcyber/walkoff

### Natively

If the Python environment for your elevated privileges are the same as the Python environment you will be running WALKOFF in (use `pip --version` to check), you can use the all-in-one setup script with elevated privileges:

   `python setup_walkoff.py`

If that is not the case, or if you would like to manually install WALKOFF:

First, install the dependencies with the following command:

   `pip install -r requirements.txt`

To install the dependencies for each individual app, run:

   `python scripts/install_dependencies.py`

Or to just install the dependencies for specific apps:

   `python scripts/install_dependencies.py -a AppOne,AppTwo,AppThree`
   
Then, generate certificates for WALKOFF's internal messaging:

   `python scripts/generate_certificates.py`

Next, navigate to /walkoff/client and install the client dependencies with the
following commands - these will require elevated privileges:

   `npm install`

Next, use gulp to build the client:

   `npm run build`

That's it! To start up the server, just navigate back to the WALKOFF root and
run:

   `python walkoff.py`

Then, navigate to the specified IP and port to start using WALKOFF. The default
is `http://127.0.0.1:5000`.

Through this script, you can also specify port and host, for example

    `python walkoff.py --port 3333 --host 0.0.0.0`

For more options, run

    `python walkoff.py --help`

## Features

1. Custom app interfaces
   * Interfaces are built using HTML/CSS/Javascript with back-end
     functionality using Python.

   * Capability to stream data to interfaces.

2. User and Role based authentication

3. Case based logging
   * Can granularly configure which events to log on a per-case basis

4. Drag and Drop Workflow Editor
   * Makes creation and editing of workflows as easy as dragging and dropping
     capabilities.

5. Flexible Workflow Execution
   * Manual Execution - Execute a workflow by pressing a button
   * Active Execution - Cron style workflow execution
     *Run workflow every 8 hours for the next 3 months*
   * Passive Execution - Trigger a workflow based upon data sent to Walkoff
   * Ability to pause and resume workflows enabling *human in the loop*
     execution

6. Metrics
   * How often are certain apps run?

   * How often workflows are run?

## Apps

WALKOFF-enabled apps can be found at www.github.com/nsacyber/walkoff-apps

## Branches

1. master - Main branch for WALKOFF version 2 will be updated from development
   periodically
2. development - Development branch for WALKOFF version 2.  Updated frequently
3. gh-pages - Pages used to generate documentation at our
   [github.io](https://nsacyber.github.io/WALKOFF "GitHub IO") site
4. gh-pages-development - Branch used to document new features in development.
3. walkoff-experimental - WALKOFF version 1  *No longer under development*

*Other development-centric branches may be created but should not be
considered permanent*

## Updating Walkoff

An update script, `update.py`, is provided to update the repo to the most
recent release. This script uses SqlAlchemy-Alembic to update database schemas
and custom upgrade scripts to update the workflow JSON files. To run this
script in interactive mode run `python update.py -i`. Other options can be
viewed using `python update.py --help`. The most common usage is
`python update.py -pcs` for pull, clean, and setup.

## Stability and Versioning

WALKOFF uses Semantic Versioning. Until the full feature set is developed, the
versions will begin with `0.x.y`. The `x` version will be updated when a
breaking change is made, a breaking change being defined as one which modifies
either the REST API or the API used to develop and specify the apps is modified
in a way which breaks backward compatibility. No guarantees are yet made for
the stability of the backend Python modules. The `y` version will be updated
for patches, and bug fixes. The REST API will have an independent versioning
system which may not follow Walkoff's version number.

## Contributions

WALKOFF is a community focused effort and contributions are welcome.
Please submit pull requests to the `development` branch. Issues marked
`help wanted` and `good first issue` are great places to start
contributing. Additionally, you can always look at our
[CodeClimate Issues page](https://codeclimate.com/github/nsacyber/WALKOFF/issues "CodeClimate Issues")
and help us improve our code quality.

Comments or questions?  walkoff@nsa.gov
