import time
from novaclient import client as nv_client
from cinderclient.v2 import client as cin_client

class VmSnapshot(object):
	"""
	Class for creating VMs snapshots
	"""

	def __init__(self, *args, **kwargs):
		"""
		Initializes the project credentials
		@kwargs:
			version: Client version
			user: username of the project
			password: Password of the project
			project: Name of the project
			auth_url: Athorization url fro overcloudrc file
		"""
		self.version = kwargs.pop("version", 2)
		self.user = kwargs.pop("user", "")
		self.password = kwargs.pop("password", "")
		self.project = kwargs.pop("project", "")
		self.auth_url = kwargs.pop("auth_url", "")
		self.get_nova_client()
		self.get_cinder_client()
		self.get_servers_list()

	def get_nova_client(self):
		"""
		Rreturns the nova authenticated client object
		"""
		try:
			self.nova = nv_client.Client(self.version, self.user, self.password, self.project, self.auth_url)
			self.nova.authenticate()
		except Exception as e:
			print "Error creating/authenticating nova client: %s" % e

	def get_cinder_client(self):
		"""
		Return the cinder client
		"""
		try:
			self.cinder = cin_client.Client(self.user, self.project, self.project, self.auth_url, service_type="volume")
			self.cinder.authenticate()
		except Exception as e:
			print "Error creating/authenticating cinder client: %s" % e	


	def get_servers_list(self):
		"""
		Return total server in the project
		"""
		self.servers = self.nova.servers.list()


class CreateSnapshots(VmSnapshot):
	"""
	Class for creating VMs snapshots
	"""

	def __init__(self, *args, **kwargs):
		"""
		Initializes the Create class
		"""
		super(self.__class__, self).__init__(*args, **kwargs)

	def create_all_vms_snapshot(self):
		"""
		Creates snapshots for all the VMs
		"""
		# self.get_all_images()
		for vm in self.servers:
			snap_id = self.create_vm_snapshot(vm, vm.name)

	def create_vm_snapshot(self, vm, snap_name):
		"""
		Returns the snapshot for vm object
		@args:
			vm: Handle of the server for which we need to create the snapshot
			snap_name: Name to be added to the snapshot name 
		"""
		try:
			snap_name = "snap_" + snap_name
			snap_id = self.nova.servers.create_image(vm, snap_name)
			return snap_id
		except Exception as e:
			print "Error making %s snaphot! %s" % (vm.name, e)


class DeleteSnapshots(VmSnapshot):
	"""
	Class for deleting Vms snapshots
	"""

	def __init__(self, *args, **kwargs):
		"""
		Initializes the Create class
		"""
		super(self.__class__, self).__init__(*args, **kwargs)
		self.get_all_images()
		self.get_all_volumes()

	def get_all_images(self):
		"""
		Returns list of all snapshots
		"""
		image_snapshots = self.nova.images.list()
		self.image_ids = [i.id for i in image_snapshots if "snap_" in i.name]

	def get_all_volumes(self):
		"""
		Returns list of all snapshots
		"""
		vol_snapshots = self.cinder.volumes.api.volume_snapshots.list()
		self.volume_ids = [i.id for i in vol_snapshots if "snap_" in i.display_name]

	def delete_image(self, id):
		"""
		Deletes the image with ID
		@args:
			id: Id of the image to be deleted
		"""
		try:
			self.nova.images.delete(id)
		except Exception as e:
			"Error deleting snapshot: %s for vm: %s " %(id)

	def delete_volume(self, id):
		"""
		Deletes the Volume with ID
		@args:
			id: Id of the volume to be deleted
		"""
		try:
			self.cinder.volumes.api.volume_snapshots.delete(id)
		except Exception as e:
			"Error deleting snapshot: %s for vm: %s " %(id)

	def delete_all_images(self):
		"""
		Deletes images for all servers
		"""
		for id in self.image_ids:
			self.delete_image(id)

	def delete_all_volumes(self):
		"""
		Deletes volumes for all servers
		"""
		for id in self.volume_ids:
			self.delete_volume(id)



if __name__ == '__main__':
	args = []
	kwargs = {}
	kwargs.update({"version": 2})
	kwargs.update({"user": "snap"})
	kwargs.update({"password": "snap"})
	kwargs.update({"project": "snap"})
	kwargs.update({"auth_url": "http://10.100.40.12:5000/v2.0"})
	create_obj = CreateSnapshots(*args, **kwargs)
	create_obj.create_all_vms_snapshot()
	time.sleep(30)
	delete_obj = DeleteSnapshots(*args, **kwargs)
	delete_obj.delete_all_images()
	delete_obj.delete_all_volumes()