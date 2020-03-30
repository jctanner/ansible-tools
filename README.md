# ansible-tools

Some useful tools for folks that triage/fix/debug/deal with github.com/ansible/ansible


1. ansible-workon - make a working directory and helpers for fixing an ansible issue
2. ansible-list-versions - emits a list of all the released versions of ansible
3. ansible-test-versions - runs a script with all versions or a subset of ansible
4. list-ansible-installs - inventories all the places ansible could have been installed
5. docker_killall - stop all containers
6. docker_rmall - clean up all dead container images

# installing

for end users ...
```
pip install ansible-dev-tools
```

for devs ...
```
virtualenv /tmp/atools.venv
source /tmp/atools.venv/bin/activate
git clone https://github.com/jctanner/ansible-tools
cd ansible-tools
python setup.py develop
```

# Usage

The most common thing you'll probably use from this set of tools is ansible-test-verisons ...

1. Install the package
2. ansible-workon --repo=ansible --number=60000
3. cd ~/workspace/issues/ansible-60000
4. ansible-test-versions --start=2.9.0 test.sh

The command is going to do a few things ...
* fetch all release tarballs from releases.ansible.com
* extract all the tarballs
* add a hacking/env-setup script from devel to all the extrated dirs
* iterate through releases defined by the arguments (or all) and run test.sh with them

The test.sh script is a minimal sort of "hello world" script that runs a simple playbook. Depending on what you are trying to fix or test, you'll need to edit the test.sh, site.yml, ansible.cfg and inventory files created by the ansible-workon script.
