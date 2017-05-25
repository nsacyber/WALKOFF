#!/bin/bash

CUR_DIR=$1
source $CUR_DIR/setup-parameters.sh

if [ $# -eq 0 ]; then
  TOTAL_NODES=2
else
  TOTAL_NODES=$2
fi

# Initialize and create auxiliary directories/ files as needed
DD_DIR=$CUR_DIR/dd
LOG_DIR=$DD_DIR/logs
EXTRAS_DIR=$DD_DIR/extras

COUNTER=1
echo "Begin deploying smart contract from Node #$COUNTER's account $ACCOUNT_ADDRS"
NODE_DD_DIR=$DD_DIR/dd$COUNTER
ACCOUNT_LIST=$($GETH_DIR/geth --datadir $NODE_DD_DIR account list)
ACCOUNT_ADDRS=$(echo "$ACCOUNT_LIST" | cut -d ' ' -f 3)
$CUR_DIR/step5-deploy-contract.js "$RPCPORT_PREFIX$COUNTER" "$ACCOUNT_ADDRS"

sleep 2
echo "Finished deploying smart contract from Node #$COUNTER's account $ACCOUNT_ADDRS"
echo "See 'dd/logs' for logs, and run e.g. '\$HOME/geth-linux-amd64-1.6.0-facc47cb/geth attach dd/dd1/geth.ipc' to use CLI for 1st miner."
echo "All $TOTAL_NODES nodes are configured. Ethereum network with $TOTAL_NODES miners is now running."
