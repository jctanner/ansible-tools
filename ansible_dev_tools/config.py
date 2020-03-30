#!/usr/bin/env python

import argparse
import os


# ansible-version stuff downloads bits here ...
VARCACHE = '/var/cache'
ANSIBLE_DEV_TOOLS_CACHEDIR = os.path.join(VARCACHE, 'ansible.dev.tools')
if not os.path.exists(ANSIBLE_DEV_TOOLS_CACHEDIR) and not os.access('/var/cache', os.W_OK):
    ANSIBLE_DEV_TOOLS_CACHEDIR = os.path.expanduser('~/.ansible.dev.tools')

# ansible-workon uses this to create new dirs for working issues ...
ANSIBLE_DEV_TOOLS_WORKDIR = os.path.expanduser(os.environ.get('ANSIBLE_DEV_TOOLS_WORKDIR', '~/workspace/issues'))

# keep track of what the last workdir was ...
ANSIBLE_DEV_TOOLS_WORKDIR_LOCKFILE = os.path.join(ANSIBLE_DEV_TOOLS_WORKDIR, '.current')

# make it easy to get the dir ...
ANSIBLE_DEV_TOOLS_WORKDIR_CURRENT = None
if os.path.exists(ANSIBLE_DEV_TOOLS_WORKDIR_LOCKFILE):
    with open(ANSIBLE_DEV_TOOLS_WORKDIR_LOCKFILE, 'r') as f:
        ANSIBLE_DEV_TOOLS_WORKDIR_CURRENT = f.read().strip()
