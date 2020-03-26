#!/usr/bin/env python

import argparse
import os


VARCACHE = '/var/cache'
ANSIBLE_TOOLS_CACHEDIR = os.path.join(VARCACHE, 'ansibletools')
if not os.path.exists(ANSIBLE_TOOLS_CACHEDIR) and not os.access('/var/cache', os.W_OK):
    ANSIBLE_TOOLS_CACHEDIR = os.path.expanduser('~/.ansibletools')
