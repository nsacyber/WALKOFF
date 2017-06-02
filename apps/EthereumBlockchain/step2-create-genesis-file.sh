#!/bin/bash

CUR_DIR=$1
source $CUR_DIR/setup-parameters.sh

# Initialize and create auxiliary directories/ files as needed
DD_DIR=$CUR_DIR/dd
EXTRAS_DIR=$DD_DIR/extras

echo "Begin creating genesis file"
ACCOUNT_LIST=$($GETH_DIR/geth --datadir $CUR_DIR account list)
ACCOUNT_ADDRS=$(echo "$ACCOUNT_LIST" | cut -d ' ' -f 3)
$CUR_DIR/step2-create-genesis-file.js "$ACCOUNT_ADDRS"

sleep 2
echo "Finished creating genesis file"