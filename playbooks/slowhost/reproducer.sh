#!/bin/bash

if [[ ! -d results ]]; then
    mkdir results
fi

export ANSIBLE_HOST_LIMIT=40

export ANSIBLE_VERSION=2.4.0.0
#export ANSIBLE_VERSION=2.5.9
#export ANSIBLE_VERSION=2.6.4
#export ANSIBLE_VERSION=2.7.0

LOGFILE="results/res_h${ANSIBLE_HOST_LIMIT}_v${ANSIBLE_VERSION}.log"

ansible --version > $LOGFILE
ANSIBLE_DEBUG=1 ANSIBLE_LOG_PATH=${LOGFILE}.ansible ansible-playbook -vvvv -i docker_inventory.py reproducer.yml | tee -a $LOGFILE
