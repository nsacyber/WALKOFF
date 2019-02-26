#!/bin/bash

# install_docker.sh - BASH script which automatically installs Docker CE Engine
# using the directions found on the web page at:
# https://docs.docker.com/install/
# 
# Please note, if the installation steps for Docker CE become misaligned with this
# script, i.e., this script breaks, it needs to be updated to conform to the latest 
# info found on the website listed above, or wherever that website is moved to.
#
# NOTE: This script has only been tested successfully on Ubuntu Desktop 18.04 LTS.
# NOTE: Be sure to execute this script using sudo
#
# LAST UPDATED: 26 Feb 2019
#

apt-get -y update
apt-get -y install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io

# Run the command shown below to verify that Docker is correctly installed.
docker run hello-world
