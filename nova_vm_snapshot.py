from novaclient import client as nv_client
from cinderclient.v2 import client as cin_client
import time
import os
from optparse import OptionParser


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
			self.cinder = cin_client.Client(self.user, self.password, self.project, self.auth_url, service_type="volume")
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
			snap_id = self.create_vm_snapshot(vm, vm.id)

	def create_vm_snapshot(self, vm, snap_name):
		"""
		Returns the snapshot for vm object
		@args:
			vm: Handle of the server for which we need to create the snapshot
			snap_name: Name to be added to the snapshot name 
		"""
		try:
			snap_name = "snap_" + snap_name[-9:] + "_" + str(int(time.time()))
			snap_id = self.nova.servers.create_image(vm, snap_name)
			return snap_id
		except Exception as e:
			print "Error making %s snapshot! %s" % (vm.name, e)


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
		self.sort_ids = SortExpired(self.image_snapshots, self.vol_snapshots)

	def get_all_images(self):
		"""
		Returns list of all snapshots
		"""
		self.image_snapshots = self.nova.images.list()
		self.image_ids = [i.id for i in self.image_snapshots if "snap_" in i.name]

	def get_all_volumes(self):
		"""
		Returns list of all snapshots
		"""
		self.vol_snapshots = self.cinder.volumes.api.volume_snapshots.list()
		self.volume_ids = [i.id for i in self.vol_snapshots if "snap_" in i.display_name]

	def delete_image(self, id):
		"""
		Deletes the image with ID
		@args:
			id: Id of the image to be deleted
		"""
		try:
			self.nova.images.delete(id)
		except Exception as e:
			"Error deleting snapshot: %s " %(id)

	def delete_volume(self, id):
		"""
		Deletes the Volume with ID
		@args:
			id: Id of the volume to be deleted
		"""
		try:
			self.cinder.volumes.api.volume_snapshots.delete(id)
		except Exception as e:
			"Error deleting snapshot: %s " %(id)

	def delete_all_images(self,ids):
		"""
		Deletes images for all servers
		@args:
			ids: IDS of images to delete
		"""
		for id in ids:
			self.delete_image(id)

	def delete_all_volumes(self, ids):
		"""
		Deletes volumes for all servers
		@args:
			ids: IDS of volumes to delete
		"""
		for id in ids:
			self.delete_volume(id)

	def delete_expired(self, span):
		"""
		Deletes the expired images and volumes
		@args:
			span: Total no of days to expire
		"""
		self.sort_ids.get_expired_images(span=span)
		self.sort_ids.get_expired_volumes(span=span)
		self.delete_all_images(self.sort_ids.expired_image_ids)
		self.delete_all_volumes(self.sort_ids.expired_volume_ids)


class SortExpired(object):
	"""
	Sorts the expired images and volumes
	"""

	def __init__(self, images, volumes):
		"""
		Initializes the images and volumes list
		"""
		self.images = images
		self.volumes = volumes

	def group_images(self):
		"""
		Group images of a particular VM
		"""
		images = {entity.name: entity.id for entity in self.images if len(entity.name.split("_"))==3}
		self.img_gps = self.make_groups(images)

	def group_volumes(self):
		"""
		Group volumes of a particular VM
		"""
		volumes = {entity.display_name.split()[2:][0]: entity.id for entity in self.volumes if len(entity.display_name.split("_"))==3}
		self.vol_gps = self.make_groups(volumes)	

	def make_groups(self, val):
		"""
		Groups the same entities
		"""
		vm_gp = {}
		for name, id in val.items():
			id_limit = name.split("_")[1]
			if id_limit in vm_gp.keys():
				vm_gp[id_limit].append((name,id))
			else:
				vm_gp.update({id_limit:[(name,id)]})
		return vm_gp		

	def get_expired_images(self, span=4):
		"""
		Returns all the images which are before span days
		@args:
			span: No of days for backup
		"""
		self.group_images()
		total_seconds = span*24*60*60
		current_time = time.time()
		self.expired_image_ids = self.sort_expired(self.img_gps, total_seconds, current_time)

	def get_expired_volumes(self, span=4):
		"""
		Returns all the images which are before span days
		@args:
			span: No of days for backup
		"""
		self.group_volumes()
		total_seconds = span*24*60*60
		current_time = time.time()
		self.expired_volume_ids = self.sort_expired(self.vol_gps, total_seconds, current_time)		

	def sort_expired(self, val, total_seconds, current_time):
		"""
		Sorts expired images and volumes
		@args:
			val: VAlue of images/volumes
			total_seconds: total no of seconds to expire
			current_time: current epoch time
		"""
		all_expired_ids = []
		for id in val:
			expired_ids = [i[1] for i in val[id] if self.compare_times(total_seconds, current_time, int(i[0].split("_")[2]))]
			all_expired_ids += expired_ids
		return all_expired_ids

	def compare_times(self, diff, current, prev):
		"""
		Comapres the current and previous times
		@args:
			diff: Difference of time to compare
			current: Current time
			prev: time of creation of the snapshots
		"""
		if (current - prev) > diff:
			return True
		else:
			return False


def main():
	parser = OptionParser()
	parser.add_option("-d", "--delete-span", dest="span", type="float",
						help="Total no of days for retaining the backup")
	(options, args) = parser.parse_args()
	if (options.span == None):
		print parser.usage
		exit(0)
	else:
		span = options.span
	user = os.getenv("OS_USERNAME", None)
	password = os.getenv("OS_PASSWORD", None)
	project = os.getenv("OS_TENANT_NAME", None)
	auth_url = os.getenv("OS_AUTH_URL", None)
	args = []
	kwargs = {}
	kwargs.update({"version": 2})
	kwargs.update({"user": user})
	kwargs.update({"password": password})
	kwargs.update({"project": project})
	kwargs.update({"auth_url": auth_url})
	create_obj = CreateSnapshots(*args, **kwargs)
        while True:
            print "Taking the snapshots for images and volumes"
	    create_obj.create_all_vms_snapshot()
	    time.sleep(30)
            print "Deleting the Expired snapshots!!!"
	    delete_obj = DeleteSnapshots(*args, **kwargs)
	    delete_obj.delete_expired(span)
            print "Waiting for the whole day to recreate the snapshots..."
            time.sleep(24*60*60)

if __name__ == '__main__':
	main()

