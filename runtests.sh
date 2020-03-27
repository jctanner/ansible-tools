#!/bin/bash

#PYTHONPATH=.:$PYTHONPATH nosetests -v --nocapture tests/

rm -rf /tmp/atools.testenv
virtualenv /tmp/atools.testenv
source /tmp/atools.testenv/bin/activate
python setup.py develop
pip install -r requirements.txt

ansible-tools-config --cachedir
ansible-list-versions
