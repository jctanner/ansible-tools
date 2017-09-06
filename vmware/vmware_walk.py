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
import os
import requests
import ssl
import sys

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


class Module(object):
    params = {}
    def fail_json(self, msg=None, apierror=None):
        print(msg)
        print(apierror)
        sys.exit(1)


class VMwareWalker(object):

    def __init__(self):
        self.lines = []

    def walk(self, obj, parent='', display=True, showdetail=True):

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

        if display:
            print(thispath)
        self.lines.append(thispath)

        if isinstance(obj, vim.ServiceInstanceContent):
            obj = obj.rootFolder
            self.walk(obj, parent=thispath, display=display, showdetail=showdetail)
            return
        elif isinstance(obj, vim.Folder):
            try:
                for child in obj.childEntity:
                    self.walk(child, parent=thispath, display=display, showdetail=showdetail)
            except Exception as e:
                pass
            return
        elif isinstance(obj, vim.Datacenter):
            for attrib in ['datastore', 'datastoreFolder', 'hostFolder', 'vmFolder']:
                dobj = getattr(obj, attrib)
                if not hasattr(dobj, 'count'):
                    self.walk(dobj, parent=thispath, display=display, showdetail=showdetail)
                else:
                    for dxobj in dobj:
                        self.walk(dxobj, parent=thispath, display=display, showdetail=showdetail)
            return
        elif isinstance(obj, vim.Datastore):
            for attrib in ['vm']:
                if not hasattr(obj, attrib):
                    continue
                dobj = getattr(obj, attrib)
                if not hasattr(dobj, 'count'):
                    self.walk(dobj, parent=thispath, display=display, showdetail=showdetail)
                else:
                    for dxobj in dobj:
                        self.walk(dxobj, parent=thispath, display=display, showdetail=showdetail)
            return
        elif isinstance(obj, vim.VirtualMachine):
            return
        elif isinstance(obj, vim.ComputeResource):
            for hobj in obj.host:
                self.walk(hobj, parent=thispath, display=display, showdetail=showdetail)
            return
        elif isinstance(obj, vim.HostSystem):
            try:
                for vmobj in obj.vm:
                    self.walk(vmobj, parent=thispath, display=display, showdetail=showdetail)
            except Exception as e:
                # vcsim has an issue here
                pass
            return

        raise Exception('%s is an unhandled type' % type(obj))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', default=os.environ.get('VMWARE_HOST'))
    parser.add_argument('--username', default=os.environ.get('VMWARE_USER'))
    parser.add_argument('--password', default=os.environ.get('VMWARE_PASSWORD'))
    parser.add_argument('--nodetail', action='store_true')
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
    vmw = VMwareWalker()

    if not args.filter:
        vmw.walk(content, display=True, showdetail=(not args.nodetail))
    else:
        vmw.walk(content, display=False, showdetail=(not args.nodetail))
        lines = [x for x in vmw.lines if args.filter in x]
        print '\n'.join(lines)


if __name__ == "__main__":
    main()
