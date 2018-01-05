#!/usr/bin/env python

# ~/go/bin/vcsim -dc 0 -ds 0 -cluster 0 -host 0 -vm 00 -trace

#Usage: govc folder.create [OPTIONS] PATH...
#Create folder with PATH.
#
#Examples:
#  govc folder.create /dc1/vm/folder-foo
#  govc object.mv /dc1/vm/vm-foo-* /dc1/vm/folder-foo
#  govc folder.create -pod /dc1/datastore/sdrs
#  govc object.mv /dc1/datastore/iscsi-* /dc1/datastore/sdrs
#
#Options:
#  -pod=false                  Create folder(s) of type StoragePod (DatastoreCluster)


#Usage: govc datacenter.create [OPTIONS] NAME...
#
#Options:
#  -folder=                    Inventory folder [GOVC_FOLDER]

import argparse
import os
import subprocess
import sys
from pprint import pprint


GOVC = None


def get_govc_path():

    global GOVC

    cmd = 'which govc'
    (rc, so, se) = run_command(cmd)

    if rc == 0:
        GOVC = so.strip()
    else:
        choices = ['~/go/bin/govc', '~/bin/govc']
        for choice in choices:
            path = os.path.expanduser(choice)
            if os.path.isfile(path):
                GOVC = path
                break

    return GOVC


def run_command(args, shell=True, env=None, capture=True):
    kwargs = {
        'shell': shell,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }

    if not capture:
        kwargs.pop('stdout', None)
        kwargs.pop('stderr', None)

    if env:
        kwargs['env'] = dict(env)

    p = subprocess.Popen(args, **kwargs)
    (so, se) = p.communicate()
    return (p.returncode, so, se)


def run_govc(args, hostname, username, password):

    env = os.environ.copy()
    env['GOVC_URL'] = hostname
    env['GOVC_USERNAME'] = username
    env['GOVC_PASSWORD'] = password
    env['GOVC_INSECURE'] = "1"

    govc = get_govc_path()
    if not govc:
        raise Exception('govc command not found')

    cmd = '{} {} 2>&1'.format(govc, args)
    print(cmd)
    (rc, so, se) = run_command(cmd, env=env)

    return (rc, so, se)


def get_datacenter_paths(kwargs):
    '''
    $ govc datacenter.info
    Name:                DC1A
    Path:              /topfolder2/1/a/DC1A
    ...
    Name:                DC1A
    Path:              /topfolder/1/a/DC1A
    ...
    '''

    (rc, so, se) = run_govc('datacenter.info', **kwargs)
    lines = so.split('\n')

    dcpaths = []
    for line in lines:
        line = line.strip()
        if line.startswith('Path:'):
            thispath = line.split()[-1]
            if thispath not in dcpaths:
                dcpaths.append(thispath)

    return dcpaths


def get_cluster_paths(kwargs):
    '''
    $ govc find -type c C1A
    C1A
    $ govc find -type c
    /topfolder/1/a/DC1A/host/C1A
    '''
    (rc, so, se) = run_govc('find -type c', **kwargs)
    lines = so.split('\n')
    lines = [x.strip() for x in lines if x.strip()]
    return lines


def process(args, walklines):

    kwargs = {
        'hostname': args.hostname,
        'username': args.username,
        'password': args.password
    }

    govc = get_govc_path()

    for line in walklines:

        print(line)
        if line == '/':
            continue
        if not line.startswith('/'):
            continue
        line = line.replace("'", '')
        line = line.replace('Datencenter', 'Datacenters')

        # .../[vim.Datastore:/tmp/govcsim-835818983@folder-10]LocalDS_0
        if 'Datastore' not in line:
            parts = [x for x in line.split('/') if x]
        else:
            parts = line.split('/[')
            parts = [x for x in parts if x]
            #import epdb; epdb.st()

        if not parts:
            continue

        parent = []
        datacenter_name = None

        for part in parts:

            name = part.split(']')[-1]
            if ':' in part:
                vimtype = part.split(']')[0].split(':')[0].replace('[', '')
                moid = part.split(']')[0].split(':')[1].replace('[', '')
            else:
                vimtype = None
                moid = None

            if vimtype is None:
                continue
            if moid == 'group-d1':
                continue

            print('------------------------------------------------------------')
            print(parent, name,moid,vimtype)
            print('------------------------------------------------------------')

            if vimtype in ['vim.Folder', 'vim.Datacenter', 'vim.ClusterComputeResource']:

                if vimtype == 'vim.Datacenter':

                    datacenter_name = name

                    if parent:
                        dcfolder = '/' + '/'.join(parent)
                    else:
                        dcfolder = '/'
                    if dcfolder != '/':
                        dcpath = dcfolder + '/' + name
                    else:
                        dcpath = dcfolder + name
                    if dcpath not in get_datacenter_paths(kwargs):
                        print('CREATE {}'.format(dcpath))
                        (rc, so, se) = run_govc('datacenter.create -folder={} {}'.format(dcfolder, name), **kwargs)
                        if rc != 0:
                            print(so + se)
                            sys.exit(rc)

                elif vimtype == 'vim.ClusterComputeResource':
                    cfolder = '/' + '/'.join(parent)
                    cpath = cfolder + '/' + name

                    if cpath not in get_cluster_paths(kwargs):
                        print('CREATE {}'.format(cpath))
                        cmd = 'cluster.create -folder "{}" "{}"'.format(cfolder, name)
                        (rc, so, se) = run_govc(cmd, **kwargs)
                        if rc != 0:
                            print(so + se)
                            sys.exit(rc)

                elif moid.startswith('group-') or moid.startswith('folder-'):
                    if parent:
                        thisfolder = '/' + '/'.join(parent) + '/' + name
                    else:
                        thisfolder = '/' + name
                    (rc, so, se) = run_govc('folder.info "{}"'.format(thisfolder), **kwargs)
                    print(so)
                    if rc != 0:
                        print('CREATE {}'.format(thisfolder))
                        (rc, so, se) = run_govc('folder.create "{}"'.format(thisfolder), **kwargs)
                        if rc != 0:
                            print(so + se)
                            sys.exit(rc)

                # increment the parent
                parent.append(name)

            elif vimtype == 'vim.Datastore':
                # govc datastore.info
                #   datastore.info [OPTIONS] [PATH]..
                # govc datastore.create
                #   -type nfs -name nfsDatastore -remote-host 10.143.2.232 -remote-path /share cluster1
                #   -type vmfs -name vmfsDatastore -disk=mpx.vmhba0:C0:T0:L0 cluster1
                #   -type local -name localDatastore -path /var/datastore host1

                # NEED A HOST FOR A DS!!!

                cmd = "datastore.info"
                cmd += " -dc={}".format(datacenter_name)
                import epdb; epdb.st()

            else:
                import epdb; epdb.st()

    print('FINISHED!')
    import epdb; epdb.st()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', default=os.environ.get('VMWARE_HOST'))
    parser.add_argument('--username', default=os.environ.get('VMWARE_USER'))
    parser.add_argument('--password', default=os.environ.get('VMWARE_PASSWORD'))
    parser.add_argument('walkfile')
    args = parser.parse_args()

    walkfile = os.path.expanduser(args.walkfile)
    if not os.path.exists(walkfile):
        raise Exception(walkfile + ' does not exist')

    with open(walkfile, 'rb') as f:
        walkdata = f.readlines()

    walkdata = [x.strip() for x in walkdata]
    process(args, walkdata)


if __name__ == "__main__":
    main()
