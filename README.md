# VmSnapshot
Create/Delete VM snapshot in Openstack

This is a simple script to create/delete VM snapshots using nova and
cinder client.
Nova client is used to first take the snapshots for VMs. Snapshot of
a Vm creates image and volume snapshot.
Nova client is used to delete the image snapshot and cinder client is
used to delete the volume snapshot.

Adjust the sleep time in main, after how much time snapshot should be
deleted.
