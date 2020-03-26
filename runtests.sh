#!/bin/bash

#PYTHONPATH=.:$PYTHONPATH nosetests -v --nocapture tests/

rm -rf /tmp/atools.testenv
virtualenv /tmp/atools.testenv
source /tmp/atools.testenv/bin/activate
python setup.py install

ansible-tools-config --cachedir
#ansible-tools-cachedir
#ansible-list-versions
