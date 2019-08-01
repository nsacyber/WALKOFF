#!/bin/bash

echo "Starting Walkoff Bootloader..."
[ ! "$(docker network ls | grep -w "walkoff_default")" ] && docker network create --attachable=True --driver=overlay walkoff_default
docker run --rm -it --network walkoff_default --name walkoff_bootloader \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=$(pwd),target=$(pwd) \
    --mount type=bind,source=$(pwd)/data/config.yml,target=/common_env.yml \
    -e DOCKER_HOST=unix:///var/run/docker.sock \
    -e DOCKER_HOST_IP=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+'):5000 \
    -w $(pwd) \
    walkoff_bootloader "$@"
