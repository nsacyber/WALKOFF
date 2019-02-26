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

clear
echo
echo Docker Installation Shell Script v1.0
echo
echo Welcome to install_docker.sh.  This shell script will install Docker 
echo Engine Community Edition (CE) to your system and provision users to
echo enable the use of Docker without sudo.  
echo
echo NOTE: This shell script won't work unless you used sudo to invoke it
echo on the command line.   Confirm that this was done, or press CTRL+C to
echo exit this script and run it again with sudo.
echo
read -n 1 -s -r -p "Press any key to continue"
clear
apt-get -y update
apt-get -y install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io
groupadd docker
usermod -aG docker $(logname)
clear
echo Installation of Docker CE is complete.  Now we are going to run Docker to verify that
echo it's been installed correctly.  You'll then be prompted to reboot the system to finalize
echo the provisioning of the current user so that you can run docker without having to type 
echo sudo each time.
echo
read -n 1 -s -r -p "Press any key to continue"
clear
# Run the command shown below to verify that Docker is correctly installed.
docker run hello-world
echo
echo Setup now needs to reboot your system to make all the changes to your computer
echo become effective.
echo
read -n 1 -s -r -p "Press any key to continue"
reboot

