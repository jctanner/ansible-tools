#!/usr/bin/python

import argparse
import json
import os
import subprocess
from pprint import pprint


DOCKER_USERNAME="root"
DOCKER_PASSWORD="vagrant"
CONTAINER_USERNAME="cisco"
CONTAINER_PASSWORD="redhat1234"


def run_command(cmd):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    ) 
    (so,se) = p.communicate()
    return (p.returncode, so, se)


def get_docker_hosts():
    # '10.0.0.102\tdockerhost\n',
    with open('/etc/hosts', 'r') as f:
        flines = f.readlines()
    dockerhosts = [x.strip() for x in flines if 'dockerhost' in x]
    dockerhosts = [x.replace('\t', '\n') for x in dockerhosts]
    dockerhosts = [x.split()[1].strip() for x in dockerhosts]
    return dockerhosts


def get_containers_for_host(hostname):
    cmd = '/bin/sshpass -p %s ssh -o StrictHostkeyChecking=no' % DOCKER_PASSWORD
    cmd += ' %s@%s' % (DOCKER_USERNAME,hostname)
    cmd += ' "docker ps -a"'
    (rc, so, se) = run_command(cmd)

    containers = {}
    for line in so.split('\n'):
        if line.strip().startswith('CONTAINER'):
            continue
        parts = line.split()
        if not parts:
            continue
        containers[parts[0]] = {
            'id': parts[0],
            'name': parts[-1],
            'image': parts[1],
            'ansible_port': int(parts[-2].split(':')[-1].split('-')[0]),
            'ansible_host': hostname,
            'ansible_user': CONTAINER_USERNAME,
            'ansible_ssh_pass': CONTAINER_PASSWORD,
            #'ansible_python_interpreter': '/usr/bin/python3',
            'device_os': 'cisco-ios',
            'cli': {
                'username': CONTAINER_USERNAME,
                'host': hostname,
                'port': int(parts[-2].split(':')[-1].split('-')[0]),
                'password': CONTAINER_PASSWORD
            }
        }

    return containers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', default=None)

    docker_hosts = get_docker_hosts()

    containers = {}
    for dh in docker_hosts:
        containers.update(get_containers_for_host(dh))

    INV = {'_meta': {'hostvars': {}}}
    INV['all'] = {'hosts': []}

    for k,v in containers.items():
        INV['_meta']['hostvars'][v['name']] = v.copy()
        INV['all']['hosts'].append(v['name'])

    print(json.dumps(INV, indent=2))


if __name__ == "__main__":
    main()
