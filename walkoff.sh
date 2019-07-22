#!/bin/bash

echo "Starting Walkoff Bootloader..."
docker run --rm -it --name walkoff_bootloader \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=$(pwd),target=$(pwd) \
    --mount type=bind,source=$(pwd)/data/config.yml,target=/common_env.yml \
    -e DOCKER_HOST=unix:///var/run/docker.sock \
    -e DOCKER_REGISTRY=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+'):5000 \
    -w $(pwd) \
    walkoff_bootloader "$@"
