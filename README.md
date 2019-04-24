## 1.0 Update Overview

WALKOFF 1.0 is intended to present a more robust and scalable implementation of Apps and Workers. 
Due to the scale of the changes, this should be considered an alpha version of WALKOFF 1.0, and is for testing and 
evaluation only. **There is much work to be done, and it is not stable, feature-complete or production-ready.**

In the coming weeks, we will be continually releasing bugfixes, documentation, and tests to bring this to a stable 
state and begin adding non-core functionality. See [our roadmap](ROADMAP.md) for more details. You can also follow [the changelog](CHANGELOG.md) to keep up with the latest changes.

If you do test this out, please submit issues here when you encounter any bugs or have any suggestions so we can 
continue to improve the WALKOFF platform. 

For app development instructions, see [the app SDK](app_sdk/README.md).

If you would like to view version 0.9.4, see [the master branch](https://github.com/nsacyber/WALKOFF/tree/master). 

## Requirements

* Docker 18.06.0+: https://docs.docker.com/install/
* Docker Compose 3+ (on Linux): https://docs.docker.com/compose/install/
    * Docker Desktop for Mac and Windows are already bundled with Docker Compose.
    

## Installation

Ensure that you have Docker and Docker Compose installed.

Ensure that ports 6379 (Redis), 5432 (PostgreSQL), 5000 (Docker Registry), and 8080 (WALKOFF UI) are available, 
or configuration will be needed.

```
# Clone this repo & branch:
git clone -b 1.0.0-alpha.1 https://github.com/nsacyber/WALKOFF.git

# Navigate to where the docker-compose.yml is:
cd WALKOFF

# Walkoff 1.0 makes use of Docker Swarm - initialize one now:
docker swarm init

# Build and launch the docker-compose (this will take a while):
docker-compose up -d --build

# Follow logs for services (append service names from the docker-compose.yml to follow specific services):
docker-compose logs -f api_gateway

# UI is viewable at http://localhost:8080
```
