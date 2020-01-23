#!/bin/bash

BUILDARG="^-[a-zA-Z]*b|--build"
CLEANARG="^-[a-zA-Z]*c|--clean"
WALK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ $WALK_DIR != $PWD ]; then
  echo "Exiting because you aren't running the walkoff.sh script from within /WALKOFF"
  exit
fi

echo "Starting WALKOFF Bootloader..."

if [ ! "$(docker image ls | grep -w "walkoff_bootloader")" ]; then
  echo "Building WALKOFF Bootloader as the image didn't exist..."
  docker build -t walkoff_bootloader -f bootloader/Dockerfile $WALK_DIR
fi

for var in "$@"
do
  if [[ $var =~ $BUILDARG ]]; then
    echo "Building WALKOFF Bootloader as you specified -b or --build..."
    docker build -t walkoff_bootloader -f bootloader/Dockerfile $WALK_DIR
    break
  fi
done

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

for var in "$@"
do
  if [[ $var =~ $CLEANARG ]]; then
    printf "Removing walkoff_network network: "
    docker network rm walkoff_network
    break
  fi
done