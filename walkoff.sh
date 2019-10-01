#!/bin/bash

BUILDARG="^-[a-zA-Z]*b|--build"
if [[ $1 == "up" ]]; then
  for var in "$@"
  do
    if [[ $var =~ $BUILDARG ]]; then
      echo "Preparing WALKOFF Bootloader..."
      docker build -t walkoff_bootloader -f bootloader/Dockerfile .
    fi
  done
fi

echo "Starting WALKOFF Bootloader..."

if [ ! "$(docker network ls | grep -w "walkoff_network")" ]; then
  printf "Creating walkoff_network network: "
  docker network create --attachable=True --driver=overlay walkoff_network
fi

docker run --rm -it --network walkoff_network --name walkoff_bootloader \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=$(pwd),target=$(pwd) \
    --mount type=bind,source=$(pwd)/data/config.yml,target=/common_env.yml \
    -e DOCKER_HOST=unix:///var/run/docker.sock \
    -w $(pwd) \
    walkoff_bootloader "$@"


CLEANARG="^-[a-zA-Z]*c|--clean"
if [[ $1 == "down" ]]; then
  for var in "$@"
  do
    if [[ $var =~ $CLEANARG ]]; then
      printf "Removing walkoff_network network: "
      docker network rm walkoff_network
    fi
  done
fi
