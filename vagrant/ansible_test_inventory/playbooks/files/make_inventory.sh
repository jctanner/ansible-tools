#!/bin/bash

cgcreate -a awx:awx -t awx:awx -g memory:ansible_profile

# the script is an unusable standalone entity
tower-cli inventory_script create \
    -v \
    --insecure \
    --organization=Default \
    --script=@docker_inventory.py \
    --name=docker_inventory_script

# an inventory is NOT the script but must exist
tower-cli inventory create \
    -v \
    --insecure \
    --organization=Default
    -n test2 

# the inventory must have a "source" that points at the script
tower-cli inventory_source create \
    --name=test_source2 \
    --insecure \
    --source=custom  \
    --source-script=docker_inventory \
    --inventory=test2

tower-cli project create \
    -n DEMO_PROJECT \
    --organization=Default \
    --local-path=DEMO_PROJECT \
    --scm-type=manual \
    --force-on-exists

tower-cli job_template create \
	--name TEST_TEMPLATE \
	--inventory=test \
	--project=DEMO_PROJECT \
	--playbook=site.yml

tower-cli job launch --job-template=TEST_TEMPLATE 

tower-cli job stdout -v --job-template=TEST_TEMPLATE
tower-cli job stdout -v --job-template=TEST_TEMPLATE 4



##############################################
#	CALLBACK
##############################################

yum -y install libcgroup-tools

CGROUP_MAX_MEM_FILE=/sys/fs/cgroup/memory/ansible_profile/memory.max_usage_in_bytes
CGROUP_CUR_MEM_FILE=/sys/fs/cgroup/memory/ansible_profile/memory.usage_in_bytes
