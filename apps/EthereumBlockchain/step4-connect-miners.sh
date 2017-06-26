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

echo "Begin connecting nodes together"
COUNTER=0
while [ $COUNTER -lt $TOTAL_NODES ]; do
  let COUNTER=COUNTER+1
  ENODE=$(cat $LOG_DIR/$COUNTER.log | grep enode | sed 's/.*"\(.*\)@.*/\1/')
  ENODE=$ENODE@127.0.0.1:$PORT_PREFIX$COUNTER

  let COUNTER2=COUNTER+1
  while [ $COUNTER2 -ne $COUNTER ]; do
    if [ ! $COUNTER2 -gt $TOTAL_NODES ]; then
      NODE_DD_DIR=$DD_DIR/dd$COUNTER2
      echo "Connect Node #$COUNTER to Node #$COUNTER2"
      $GETH_DIR/geth --exec "admin.addPeer(\"$ENODE\")" attach $NODE_DD_DIR/geth.ipc
    fi
    if [ $COUNTER2 -gt $TOTAL_NODES ]; then
      COUNTER2=1
    else
      let COUNTER2=COUNTER2+1
    fi
  done
done

sleep 2
echo "Finished connecting all nodes together"