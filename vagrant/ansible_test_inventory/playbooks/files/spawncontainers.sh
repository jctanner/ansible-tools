#!/bin/bash

for ID in $(seq 1 100); do
    CNAME="sshd_${ID}"
    docker port $CNAME 22 || docker run -d -P --name $CNAME rastasheep/ubuntu-sshd:18.04
done
