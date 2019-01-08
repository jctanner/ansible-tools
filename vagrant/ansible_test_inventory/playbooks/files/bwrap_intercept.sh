#!/bin/bash

# * yum install strace ... don't forget this =)
# * Place this file into /usr/local/bin/bwrap so that it takes
#   precedence over /bin/bwrap in the path.
# * chmod +x /usr/local/bin/bwrap

echo "STARTING" >> /tmp/bwrap.log
env >> /tmp/bwrap.log
echo "INARGS: $@" >> /tmp/bwrap.log

CGROUP_PREFIX=/sys/fs/cgroup/memory/ansible_profile
export ANSIBLE_CALLBACK_WHITELIST=baseline,cgroup_memory_recap
export CGROUP_MAX_MEM_FILE=$CGROUP_PREFIX/memory.max_usage_in_bytes
export CGROUP_CUR_MEM_FILE=$CGROUP_PREFIX/memory.usage_in_bytes

TEST_ARGS=""
NEWARGS=$(echo "$@" | sed "s|ansible-playbook|$TEST_ARGS ansible-playbook|")
echo "NEWARGS: $NEWARGS" >> /tmp/bwrap.log

/bin/bwrap $NEWARGS
