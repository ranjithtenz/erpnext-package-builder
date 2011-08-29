import os, sys
from build_settings import *

def build():
	make_master()
	make_tarball()

def run_patches():
	"""
		Run the latest patches in the master
	"""
	print "Running Patches..."
	import webnotes
	from webnotes.modules import patch
	import webnotes.profile

	webnotes.conn = Database('localhost','root', root_password)
	webnotes.conn.use('_tmpmaster')
	webnotes.session = {'user':'Administrator'}
	webnotes.user = webnotes.profile.Profile()
	patch.run()
	if webnotes.conn.in_transaction:
		webnotes.conn.commit()

def make_master():
	"""
		restore the master in a tmp database, run patches and export it
	"""
	# restore the master
	print "Importing master..."

	from webnotes.install_lib.install import Installer
	import webnotes
	from webnotes.db import Database

	# unzip master
	os.system("gunzip %s" % os.path.join(erpnext_path, 'master.sql.gz'))

	installer = Installer('root', root_password)
	installer.import_from_db('_tmpmaster', os.path.join(erpnext_path,'master.sql'))

	# run patches
	run_patches()

	# export db
	print "Taking fresh dump..."
	mysql_dump()

	# drop db
	print "Cleaning up..."
	webnotes.conn.sql("drop database _tmpmaster")
	os.remove(os.path.join(erpnext_path, 'master.sql'))

def mysql_dump(gzip=1):
	"""
		Take MySQL Dump of the specified database
			
		'gzip' argument toggles compression of the dump file	
	"""	
	gzip_str = '| gzip -c > %(target)s.sql.gz'
	no_gzip_str = '> %(target)s.sql'
		
	os.system('mysqldump %(db)s -u root -p%(pwd)s --ignore-table=%(db)s.__DocTypeCache --ignore-table=%(db)s.__SessionCache %(gzip)s' % \
		{
			'db': '_tmpmaster',
			'pwd':root_password.replace(' ', '\ '), 
			'gzip':(gzip and gzip_str or no_gzip_str)
		} % {
			'target':os.path.join(erpnext_path, 'master'),
		})

def tar_exclude(tarinfo):
	"""
		exclude temp files and defs.py
	"""
	if tarinfo.endswith('.pyc'): return True
	if tarinfo.endswith('.DS_Store'): return True
	if tarinfo.endswith('defs.py'): return True
	if tarinfo.startswith('.git'): return True

	return False

def tar_filter(tarinfo):
	"""
		exclude temp files and save relative path
		use in 2.7!!!
	"""
	if tarinfo.name.endswith('.pyc'): return None
	if tarinfo.name.endswith('.DS_Store'): return None
	if tarinfo.name.endswith('defs.py'): return None
	if tarinfo.name.startswith('.git'): return None

	tarinfo.name = os.path.relpath(tarinfo.name, os.path.dirname(__file__))

	return tarinfo

def make_tarball():
	"""
		make a tarball of erpnext, wnframework folders excluding defs.py and .pyc files
	"""
	print "Making tarball..."

	import erpnext_version
	import tarfile

	tar = tarfile.open("erpnext-%s.tar" % erpnext_version.version, "w:gz")
	
	# add wnframework
	tar.add(wnframework_path, arcname='wnframework', exclude=tar_exclude)
	tar.add(erpnext_path, 'erpnext', filter=tar_filter)
	tar.add(os.path.join(os.path.dirname(__file__),'install.py'), arcname='install.py')	
	tar.add(os.path.join(os.path.dirname(__file__),'install_settings.py'), arcname='install_settings.py')
	tar.add(os.path.join(os.path.dirname(__file__),'README'), arcname='README')

	tar.close()

if __name__=='__main__':
	sys.path.append(os.path.join(wnframework_path, 'cgi-bin'))
	sys.path.append(erpnext_path)
	import webnotes
	import webnotes.defs
	webnotes.defs.modules_path = erpnext_path
	#build()
	make_tarball()
	
