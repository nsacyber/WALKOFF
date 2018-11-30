[![Build Status](https://img.shields.io/travis/nsacyber/WALKOFF/master.svg?maxAge=3600&label=Linux)](https://travis-ci.org/nsacyber/WALKOFF) [![Build status](https://ci.appveyor.com/api/projects/status/hs6ujwd1f87n39ut/branch/master?svg=true)](https://ci.appveyor.com/project/iadgovuser11/walkoff/branch/master)
[![Maintainability](https://api.codeclimate.com/v1/badges/330249e13845a07a69a2/maintainability)](https://codeclimate.com/github/iadgov/WALKOFF/maintainability)[![GitHub (pre-)release](https://img.shields.io/github/release/nsacyber/WALKOFF/all.svg?style=flat)](release)


<img src="https://nsacyber.github.io/WALKOFF/files/images/flyingLogoWithTextSmall.png">

# Table of Contents

* [Description](#Description)
* [Requirements](#Requirements)
* [Installation](#Installation)
  * [Docker](#Docker)
  * [Kubernetes](#Kubernetes)
  * [Natively](#Natively)
* [Features](#Features)
* [Apps](#Apps)
* [Branches](#Branches)
* [Updating Walkoff](#Updating-Walkoff)
* [Stability and Versioning](#Stability-and-Versioning)
* [Contributions](#Contributions)
  

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

# Requirements

* Python 2.7+ or Python 3.4+
* Redis 5+
    * Redis can be run on Linux (see https://redis.io/topics/quickstart or check your OS's package manager), 
    * If you are using Windows, you will need to use Redis in a VM or a Docker container.
* Best used with Linux, or in Docker
    * On Linux, you will need the `python-devel` package for your distribution if running natively.

*Individual apps may specify their own requirements.*

# Installation

There are three main ways of using WALKOFF - natively, using Docker, or using Kubernetes.

- Natively means running WALKOFF as a Python application on your computer. This is recommended for development.
- Docker allows you to run WALKOFF inside a container that provides a consistent and portable environment. This is recommended for checking out the project, or development if you have issues with Python versioning.
- Kubernetes allows you to run WALKOFF inside a cluster for purposes of scalability and load balancing. This is recommended for networks larger than toy examples. While an initial version exists, this is also under active development.

### Docker

You can use Docker Compose to install WALKOFF along with Postgres and Redis using the compose file below. 
(This file is provided in the repository under )

Docker Compose is included with Docker CE on Linux and MacOS, but will need to be installed separately (see https://docs.docker.com/compose/install/ for more details.)

Once installed, create a file called `docker-compose.yaml` as below (or clone this repository, the file is provided under `k8s_manifests/dockerfiles/walkoff-combined/docker-compose.yaml`)

```yaml
version: '3'
services:
  walkoff:
    ports:
    - "8080:8080"
    image: "walkoffcyber/walkoff:combinedv1"
    environment:
    - "CACHE={\"type\": \"redis\", \"host\": \"walkoff-redis\", \"port\": 6379}"
    - "HOST=0.0.0.0"
    - "PORT=8080"
    - "ZMQ_RESULTS_ADDRESS=tcp://0.0.0.0:5556"
    - "ZMQ_COMMUNICATION_ADDRESS=tcp://0.0.0.0:5557"
    - "WALKOFF_DB_TYPE=postgresql"
    - "EXECUTION_DB_TYPE=postgresql"
    - "DB_PATH=walkoff"
    - "EXECUTION_DB_PATH=execution"
    - "WALKOFF_DB_HOST=walkoff-postgres"
    - "EXECUTION_DB_HOST=walkoff-postgres"
    - "EXECUTION_DB_USERNAME=walkoff"
    - "EXECUTION_DB_PASSWORD=walkoff"
    - "WALKOFF_DB_USERNAME=walkoff"
    - "WALKOFF_DB_PASSWORD=walkoff"
    depends_on:
    - "walkoff-redis"
    - "walkoff-postgres"
    # entrypoint: 
    # - "sleep" 
    # - "36000"
    # volumes:
    # - /path/to/host/apps:/app/walkoff/apps
  walkoff-redis:
    image: "redis"
  walkoff-postgres:
    image: "postgres"
    environment:
    - "POSTGRES_USER=walkoff"
    - "POSTGRES_PASSWORD=walkoff"
```

Alternatively:

```
# If you haven't created your own docker-compose.yaml, clone the respository and cd into it
git clone https://github.com/nsacyber/WALKOFF.git
cd WALKOFF/k8s_manifests/dockerfiles/walkoff-combined
```

Once you have configured the Compose file as desired and are in the same directory as it, you can start the containers:
```
# Start containers
docker-compose up
```

#### Passwords

If you would like to set usernames and passwords for your Redis or Postgres containers, ensure that they are consistent in your docker-compose.yaml, and that proper permissions are set on the file to protect it.

#### Development 

If you intend to use the container for development, you may want to run WALKOFF manually inside the container to test your changes. To do this, uncomment the "entrypoint" line and its entries.

You can also mount a volume to directories inside the container, for example if you are developing apps and would like to mount it to WALKOFF's app directory, a commented example is provided above. Alternatively, you can use the docker cp command to copy files into the container. (See https://docs.docker.com/engine/reference/commandline/cp/ for more details.)

If you uncommented the `sleep` entrypoint for development purposes, you will need to start WALKOFF yourself:
```
# Obtain the WALKOFF container ID - look for/grep 'walkoffcyber/walkoff:combinedv1'
docker ps

# Enter the container (you can use the first three characters of the ID for short)
docker exec -it abc /bin/bash

# Once inside the container, run WALKOFF:
python walkoff.py
```


### Kubernetes

Prerequisites: 
- Stand up a managed Kubernetes cluster (for development purposes, minikube is recommended: https://kubernetes.io/docs/setup/minikube/)
- Install Helm to that cluster (see https://docs.helm.sh/using_helm/ for more details)

You can then use `python -m walkoff install` to run a guided wizard that will set up resources for WALKOFF using helm and kubectl.

The steps break down as follows (see `online_install()` in `walkoff/cli/install.py` for details):

1. Create a namespace for WALKOFF if needed (not required, use default if you don't)
2. Generate ZMQ certificates and store the public/private keys in Kubernetes secrets
3. Prompt for an existing Redis instance and password, else install one to the cluster using Helm
4. Prompt for an existing PostgreSQL instance, username, and password, else install two to the cluster using Helm
5. Prompt for an existing CA signing keypair, else create one and store them in Kubernetes secrets
6. Install cert-manager (https://github.com/jetstack/cert-manager) to the cluster to generate SSL certificates for ingress
7. Install WALKOFF to the cluster using Helm with collected configuration details.

If the installation goes wrong or you change your mind, you can use `python -m walkoff uninstall` to rollback changes that the wizard made (you must do this before attempting another install). 

### Natively

We recommend using a Python virtual environment (such as venv included with Python 3, pyenv-virtualenv or pipenv),
as this avoids package version conflicts with other applications that you might have, and avoids the necessity of 
running setup with sudo, which could cause permissions issues if you don't use sudo for subsequent runs.

We also recommend using nvm to install NodeJS and npm for the same reasons as above, and as it ensures that you receive 
the latest version (or latest LTS, whichever you prefer). Some distributions (notably Ubuntu) will have very out of 
date versions of nodejs in their default repositories, as well as packages distributed with a nodejs executable instead 
of node. 

Install Redis Server:
* MacOS: Use homebrew - https://brew.sh/
* Linux: Use your distro's package manager, follow an appropriate guide for your distro.
* Windows: There are no up-to-date Redis binaries available for Windows, see Docker below.
* Docker: Run a Redis container with port 6379 published to localhost: `docker run --name walkoff-redis -p 6379:6379 -d redis`

If the Python environment for your elevated privileges are the same as the Python environment you will be running 
WALKOFF in (check that `pip --version` aligns with `which python`), you can use the all-in-one setup script with elevated privileges:

    python setup_walkoff.py

If that is not the case, or if you would like to manually install WALKOFF:

First, install Python dependencies with the following command:

    pip install -r requirements.txt

To install the Python dependencies for each individual app, run:

    python scripts/install_dependencies.py

Or to just install the dependencies for specific apps:

    python scripts/install_dependencies.py -a AppOne,AppTwo,AppThree
   
Then, generate certificates for WALKOFF's internal messaging:

    python scripts/generate_certificates.py

If you were previously familiar with WALKOFF, NodeJS and NPM are no longer needed to build front-end components, as the webpacked JavaScript files are now included in this repository.

That's it! To start up the server, just navigate back to the WALKOFF root and
run:

    python walkoff.py

Then, navigate to the specified IP and port to start using WALKOFF. The default
is `http://127.0.0.1:5000`.

Through this script, you can also specify port and host, for example

    python walkoff.py --port 3333 --host 0.0.0.0

For more options, run

    python walkoff.py --help

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

*Other development-centric branches may be created but should not be
considered permanent*

## Updating Walkoff

An update script, `python -m walkoff local update`, is provided to update your local repo to the most
recent release. This script uses SqlAlchemy-Alembic to update database schemas. Updating WALKOFF in Kubernetes is a work in progress.

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
