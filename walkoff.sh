#!/bin/bash

#echo "Preparing Walkoff Bootloader..."

#docker build -t walkoff_bootloader -f bootloader/Dockerfile .

echo "Starting Walkoff Bootloader..."

[ ! "$(docker network ls | grep -w "walkoff_default")" ] && docker network create --attachable=True --driver=overlay walkoff_default

docker run --rm -it --network walkoff_default --name walkoff_bootloader \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=$(pwd),target=$(pwd) \
    --mount type=bind,source=$(pwd)/data/config.yml,target=/common_env.yml \
    -e DOCKER_HOST=unix:///var/run/docker.sock \
    -w $(pwd) \
    walkoff_bootloader "$@"
