#!/bin/bash

#PYTHONPATH=.:$PYTHONPATH nosetests -v --nocapture tests/

rm -rf /tmp/atools.testenv
virtualenv /tmp/atools.testenv
source /tmp/atools.testenv/bin/activate
pip install ansible-dev-tools
RC=$?
if [[ $RC != 0 ]]; then
    echo "ERROR! installing from pypi"
    exit $RC
fi

# for ansible ...
pip install jinja2 PyYAML

ansible-tools-config --cachedir
ansible-tools-config --workdir
ansible-list-versions

rm -rf /tmp/test
ANSIBLE_DEV_TOOLS_WORKDIR=/tmp/test ansible-workon --number=0001
RC=$?
if [[ $RC != 0 ]]; then
    echo "ERROR running ansible-workon"
    exit $RC
fi

cd /tmp/test/ansible-0001
find .

ansible-test-versions --help
ansible-test-versions --version=2.9.0 test.sh

ansible-test-version 2.8.0 test.sh
