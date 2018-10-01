# VMSnapshot
Create/Delete VM snapshot in Openstack

This is a simple script to create/delete VM snapshots using nova and
cinder client.
Nova client is used to first take the snapshots for VMs. Snapshot of
a Vm creates image and volume snapshot.
Nova client is used to delete the image snapshot and cinder client is
used to delete the volume snapshot.

## HOW TO USE;

`source overcloudrc`

`python nova_vm_snapshot.py --delete-span 4 |tee /var/run/snapshot.log`

