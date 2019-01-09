#!/bin/bash

CONTAINER="cisco/ios-sim:latest"
for ID in $(seq 1 100); do
    CNAME="ios_${ID}"
    docker port $CNAME 22 || docker run -d -P --name $CNAME $CONTAINER
done
