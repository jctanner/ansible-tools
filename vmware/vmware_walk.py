#!/usr/bin/env python

# vmware_walk.py - walk through the inventory content in esx or vcenter
#
# Each line of output represents the full path to an object in the "content".
# Every element in the path is in the form of ['<TYPE>:<OBJECTID>']<NAME>
#
# Example:
#   vcsim -httptest.serve localhost:443 &
#   ./vmware_walk.py --hostname=localhost --username=user --password=passb | fgrep VM | fgrep -v Datastore | head
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-4']host/['vim.ComputeResource:computeresource-23']DC0_H0/['vim.HostSystem:hostsystem-21']DC0_H0/['vim.VirtualMachine:virtualmachine-61']DC0_H0_VM0
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-4']host/['vim.ComputeResource:computeresource-23']DC0_H0/['vim.HostSystem:hostsystem-21']DC0_H0/['vim.VirtualMachine:virtualmachine-65']DC0_H0_VM1
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-4']host/['vim.ClusterComputeResource:clustercomputeresource-28']DC0_C0/['vim.HostSystem:hostsystem-34']DC0_C0_H0/['vim.VirtualMachine:virtualmachine-73']DC0_C0_RP0_VM1
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-4']host/['vim.ClusterComputeResource:clustercomputeresource-28']DC0_C0/['vim.HostSystem:hostsystem-52']DC0_C0_H2/['vim.VirtualMachine:virtualmachine-69']DC0_C0_RP0_VM0
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-3']vm/['vim.VirtualMachine:virtualmachine-61']DC0_H0_VM0
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-3']vm/['vim.VirtualMachine:virtualmachine-65']DC0_H0_VM1
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-3']vm/['vim.VirtualMachine:virtualmachine-69']DC0_C0_RP0_VM0
#   .../['vim.Datacenter:datacenter-2']DC0/['vim.Folder:folder-3']vm/['vim.VirtualMachine:virtualmachine-73']DC0_C0_RP0_VM1

import argparse
import atexit
import itertools
import os
import requests
import ssl
import sys

from pprint import pprint

from pyVim import connect
from pyVmomi import vim


def connect_to_api(module, disconnect_atexit=True):

    # https://raw.githubusercontent.com/ansible/ansible/devel/lib/ansible/module_utils/vmware.py

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    validate_certs = module.params['validate_certs']

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg='pyVim does not support changing verification mode with python < 2.7.9. Either update '
                             'python or or use validate_certs=false')

    try:
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password)
    except vim.fault.InvalidLogin as invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except (requests.ConnectionError, ssl.SSLError) as connection_error:
        if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(connection_error) and not validate_certs:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)
        else:
            module.fail_json(msg="Unable to connect to vCenter or ESXi API on TCP/443.", apierror=str(connection_error))
    except Exception as e:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    return service_instance.RetrieveContent()


def fuzz_paths(paths):
    fpaths = []
    total = len(paths)
    for chunksize in xrange(0, total):
        fpaths += [x for x in itertools.combinations(paths, chunksize)]
    return fpaths


class Module(object):
    params = {}

    def fail_json(self, msg=None, apierror=None):
        print(msg)
        print(apierror)
        sys.exit(1)


class VMwareWalker(object):

    def __init__(self, content=None):
        self.content = content
        self.si = self.content.searchIndex
        self.lines = []
        self.valid_inventory_paths = []
        self.invalid_inventory_paths = []

    def walk(self, obj, parent='', display=True, filter=None, showdetail=True, fuzzytest=False):

        kwargs = {
            'parent': parent,
            'display': display,
            'filter': filter,
            'showdetail': showdetail,
            'fuzzytest': fuzzytest
        }
        #pprint(kwargs)
        #print('in: ' + parent)

        name = None
        if hasattr(obj, 'name'):
            name = obj.name
        if isinstance(obj, vim.ServiceInstanceContent):
            this_type = 'ServiceInstanceContent'
            name = 'Content'
        else:
            this_type = str(obj)

        # append to parent and display
        if showdetail:
            thispath = parent + '/' + '[' + this_type + ']' + str(name)
        else:
            thispath = parent + '/' + str(name)
        kwargs['parent'] = thispath

        if display:
            if filter and filter in thispath:
                print(thispath)
            elif not filter:
                print(thispath)
        self.lines.append(thispath)

        # test all possible paths to find this VM with findbyinventorypath
        if (fuzzytest and isinstance(obj, (vim.Folder, vim.VirtualMachine)) and not filter) or \
                (fuzzytest and isinstance(obj, (vim.Folder, vim.VirtualMachine)) and (filter and filter in obj.name)):

            try:
                self.fuzz_vm_inventory_paths(obj, thispath, showdetail=showdetail)
            except Exception as e:
                print(e)
                sys.exit(1)

        if isinstance(obj, vim.ServiceInstanceContent):
            obj = obj.rootFolder
            #self.walk(obj, parent=thispath, display=display, showdetail=showdetail, fuzzytest=fuzzytest)
            self.walk(obj, **kwargs)
            return
        elif isinstance(obj, vim.Folder):
            try:
                for child in obj.childEntity:
                    self.walk(child, **kwargs)
            except Exception as e:
                pass
            return
        elif isinstance(obj, vim.Datacenter):
            for attrib in ['datastore', 'datastoreFolder', 'hostFolder', 'vmFolder']:
                dobj = getattr(obj, attrib)
                if not hasattr(dobj, 'count'):
                    self.walk(dobj, **kwargs)
                else:
                    for dxobj in dobj:
                        self.walk(dxobj, **kwargs)
            return
        elif isinstance(obj, vim.Datastore):
            for attrib in ['vm']:
                if not hasattr(obj, attrib):
                    continue
                dobj = getattr(obj, attrib)
                if not hasattr(dobj, 'count'):
                    self.walk(dobj, **kwargs)
                else:
                    for dxobj in dobj:
                        self.walk(dxobj, **kwargs)
            return
        elif isinstance(obj, vim.VirtualMachine):
            return
        elif isinstance(obj, vim.ComputeResource):
            for hobj in obj.host:
                self.walk(hobj, **kwargs)
            return
        elif isinstance(obj, vim.HostSystem):
            try:
                for vmobj in obj.vm:
                    self.walk(vmobj, **kwargs)
            except Exception as e:
                # vcsim has an issue here
                pass
            return

        raise Exception('%s is an unhandled type' % type(obj))

    def fuzz_vm_inventory_paths(self, obj, thispath, showdetail=False):
        dirs = thispath.split('/')
        dirs = [x.strip() for x in dirs if x.strip()]
        if showdetail:
            _dirs = dirs[:]
            for idd,dirn in enumerate(_dirs):
                if ']' in dirn:
                    dirs[idd] = dirn.split(']', 1)[-1]

        folder_res = None
        if not folder_res:
            #print('fuzz the paths')
            _dirs = dirs[:] + ['vm']
            _dirs = [x.strip() for x in _dirs if x.strip()] + [obj.name]
            fpaths = fuzz_paths(_dirs)

            for fpath in fpaths:
                if not fpath:
                    continue

                # test the preceding slash too
                _paths = ['/'.join(fpath), '/' + '/'.join(fpath)]

                for _path in _paths:

                    # search each path only once
                    if _path in self.valid_inventory_paths or _path in self.invalid_inventory_paths:
                        continue

                    try:
                        folder_res = self.si.FindByInventoryPath(_path)
                    except Exception as e:
                        folder_res = None

                    if not folder_res or folder_res is None:
                        self.invalid_inventory_paths.append(_path)

                    if folder_res:
                        self.valid_inventory_paths.append(_path)
                        if showdetail:
                            print('# {}'.format(_path))
                            print('> {} [{}]'.format(folder_res.name, folder_res))
                            if hasattr(folder_res, 'vmFolder'):
                                print('>> {}'.format(folder_res.vmFolder.name))
                        if hasattr(folder_res, 'childEntity'):
                            #import epdb; epdb.st()
                            for ce in folder_res.childEntity:
                                if hasattr(ce, 'name'):
                                    if showdetail:
                                        print('>> {}'.format(ce.name))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', default=os.environ.get('VMWARE_HOST'))
    parser.add_argument('--username', default=os.environ.get('VMWARE_USER'))
    parser.add_argument('--password', default=os.environ.get('VMWARE_PASSWORD'))
    parser.add_argument('--nodetail', action='store_true')
    parser.add_argument('--fuzzytest', action='store_true')
    parser.add_argument('--filter')
    args = parser.parse_args()

    module = Module()
    module.params = {
        'hostname': args.hostname,
        'username': args.username,
        'password': args.password,
        'validate_certs': False,
    }

    content = connect_to_api(module)
    vmw = VMwareWalker(content=content)
    kwargs = {
        'display': True,
        'filter': args.filter,
        'showdetail': not args.nodetail,
        'fuzzytest': args.fuzzytest
    }

    vmw.walk(content, **kwargs)
    if args.fuzzytest:
        print('')
        print('# valid inputs for findByInventoryPath')
        pprint(sorted(set([x for x in vmw.valid_inventory_paths if args.filter in x])))


if __name__ == "__main__":
    main()
