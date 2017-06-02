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

echo "Initiating nodes"
COUNTER=1
for key in $KEYSTORE_DIR/*; do
  echo "Initiate Node #$COUNTER"

  NODE_DD_DIR=$DD_DIR/dd$COUNTER
  mkdir -p $NODE_DD_DIR/keystore
  cp $key $NODE_DD_DIR/keystore
  $GETH_DIR/geth --datadir $NODE_DD_DIR init $EXTRAS_DIR/genesis.json
  $GETH_DIR/geth --datadir $NODE_DD_DIR --networkid $NETID --nodiscover --rpc --rpcaddr 0.0.0.0 --rpcapi 'db,eth,net,web3' --rpcport $RPCPORT_PREFIX$COUNTER --port $PORT_PREFIX$COUNTER --unlock 0 --password $PASSWORD_FILEPATH --mine 2>>$LOG_DIR/$COUNTER.log &
  let COUNTER=COUNTER+1
done

sleep 2
echo "Finished: Nodes are running"
