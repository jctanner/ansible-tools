#!/bin/bash

#PYTHONPATH=.:$PYTHONPATH nosetests -v --nocapture tests/

rm -rf /tmp/atools.testenv
virtualenv /tmp/atools.testenv
source /tmp/atools.testenv/bin/activate
python setup.py develop
pip install -r requirements.txt

pip install jinja2 PyYAML

ansible-tools-config --cachedir
ansible-tools-config --workdir
ansible-list-versions

rm -rf /tmp/test
ANSIBLE_TOOLS_WORKDIR=/tmp/test ansible-workon --number=0001

cd /tmp/test/ansible-0001
find .

ansible-test-versions --help
ansible-test-versions --version=2.9.0 test.sh
