#!/bin/bash

__create_rundir() {
	mkdir -p /var/run/sshd
}

__create_hostkeys() {
ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' 
}

# Call all functions
__create_rundir
__create_hostkeys

exec "$@"
