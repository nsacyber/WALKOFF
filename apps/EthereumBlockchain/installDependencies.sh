#!/bin/bash

# install go-ethereum CLI client
wget https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.6.0-facc47cb.tar.gz
tar -xvf geth-linux-amd64-1.6.0-facc47cb.tar.gz -C $HOME > /dev/null
rm geth-linux-amd64-1.6.0-facc47cb.tar.gz

# install nodejs and npm
wget https://nodejs.org/dist/v6.10.3/node-v6.10.3-linux-x64.tar.xz
tar -xvf node-v6.10.3-linux-x64.tar.xz -C $HOME > /dev/null
rm node-v6.10.3-linux-x64.tar.xz

# install npm packages
export PATH=$HOME/node-v6.10.3-linux-x64/bin:$PATH
$HOME/node-v6.10.3-linux-x64/bin/npm install --save web3 solc
