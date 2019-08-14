#!/bin/bash

echo "Preparing Walkoff Bootloader..."

docker build -t walkoff_bootloader -f bootloader/Dockerfile .

echo "Starting Walkoff Bootloader..."

[ ! "$(docker network ls | grep -w "walkoff_default")" ] && docker network create --attachable=True --driver=overlay walkoff_default

uname_output="$(uname -s)"
case "${uname_output}" in
    Linux*)     docker_host_ip=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+');;
    *)          docker_host_ip=host.docker.internal;;
esac

echo "OS detected as $uname_output, using $docker_host_ip as target for locally-hosted services."

docker run --rm -it --network walkoff_default --name walkoff_bootloader \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=$(pwd),target=$(pwd) \
    --mount type=bind,source=$(pwd)/data/config.yml,target=/common_env.yml \
    -e DOCKER_HOST=unix:///var/run/docker.sock \
    -e DOCKER_HOST_IP=$docker_host_ip \
    -w $(pwd) \
    walkoff_bootloader "$@"
