#!/bin/bash
dnf install nfs-utils
systemctl enable nfs
systemctl restart nfs
firewall-cmd --add-service=nfs --permanent
firewall-cmd --permanent --add-service=rpc-bind
firewall-cmd --permanent --add-service=mountd
firewall-cmd --reload
