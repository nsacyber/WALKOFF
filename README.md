## Overview

WALKOFF 1.0 is intended to present a more robust and scalable implementation of Apps and Workers.

This is an alpha version of WALKOFF 1.0, with an initial working version, and is for testing and evaluation only. It is not stable, feature-complete or production-ready.

In the coming weeks, we will be continually releasing bugfixes to bring this to a stable state. See ROADMAP.md

## Requirements

* Docker: https://docs.docker.com/install/
* Docker Compose (on Linux): https://docs.docker.com/compose/install/
    * Docker Desktop for Mac and Windows are already bundled with Docker Compose.
    

## Installation

```
# Navigate to where the docker-compose.yml is
cd triple-play

# Walkoff 1.0 makes use of Docker Swarm - initialize one now
docker swarm init

# Build and launch the docker-compose (this will take a while)
docker-compose up -d --build

# View logs and follow
docker-compose logs -f

# UI is viewable at http://localhost:8080
```
