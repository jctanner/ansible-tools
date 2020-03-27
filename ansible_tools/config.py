#!/usr/bin/env python

import argparse
import os


# ansible-version stuff downloads bits here ...
VARCACHE = '/var/cache'
ANSIBLE_TOOLS_CACHEDIR = os.path.join(VARCACHE, 'ansibletools')
if not os.path.exists(ANSIBLE_TOOLS_CACHEDIR) and not os.access('/var/cache', os.W_OK):
    ANSIBLE_TOOLS_CACHEDIR = os.path.expanduser('~/.ansibletools')

# ansible-workon uses this to create new dirs for working issues ...
ANSIBLE_TOOLS_WORKDIR = os.path.expanduser(os.environ.get('ANSIBLE_TOOLS_WORKDIR', '~/workspace/issues'))
