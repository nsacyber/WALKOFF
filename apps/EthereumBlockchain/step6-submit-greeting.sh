#!/bin/bash

CUR_DIR=$1
GREETING=$2
source $CUR_DIR/setup-parameters.sh

# Initialize and create auxiliary directories/ files as needed
DD_DIR=$CUR_DIR/dd
LOG_DIR=$DD_DIR/logs
EXTRAS_DIR=$DD_DIR/extras

COUNTER=1
echo "Begin submitting new greeting from Miner #$COUNTER"
NODE_DD_DIR=$DD_DIR/dd$COUNTER
ACCOUNT_LIST=$($GETH_DIR/geth --datadir $NODE_DD_DIR account list)
ACCOUNT_ADDRS=$(echo "$ACCOUNT_LIST" | cut -d ' ' -f 3)
$CUR_DIR/step6-submit-greeting.js "$RPCPORT_PREFIX$COUNTER" "$ACCOUNT_ADDRS" "$GREETING"

sleep 2
echo "Submitted new greeting transaction from Miner #$COUNTER's account $ACCOUNT_ADDRS"
