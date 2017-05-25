#!/bin/bash

CUR_DIR=$1
source $CUR_DIR/setup-parameters.sh

if [ $# -eq 0 ]; then
  TOTAL_NODES=2
else
  TOTAL_NODES=$2
fi

# Initialize and create auxiliary directories/ files as needed
PASSWORD_FILEPATH=$CUR_DIR/password
KEYSTORE_DIR=$CUR_DIR/keystore
DD_DIR=$CUR_DIR/dd
LOG_DIR=$DD_DIR/logs
EXTRAS_DIR=$DD_DIR/extras
rm -rf $KEYSTORE_DIR $DD_DIR
mkdir -p $KEYSTORE_DIR $LOG_DIR $EXTRAS_DIR

echo "Begin creating accounts for server nodes/ miners"
COUNTER=0
while [ $COUNTER -lt $TOTAL_NODES ]; do
  $GETH_DIR/geth --datadir $CUR_DIR --password $PASSWORD_FILEPATH account new
  let COUNTER=COUNTER+1
  echo "Created Account #$COUNTER with above address"
done

sleep 2
echo "Finished creating accounts for nodes"