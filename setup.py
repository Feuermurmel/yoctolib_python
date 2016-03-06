from distutils.core import setup


setup(
	name = 'Yoctolib',
	version = '22936',
	description = 'Official Yoctopuce Library for Python',
	author = 'Yoctopuce',
	author_email = 'dev@yoctopuce.com',
	url = 'http://www.yoctopuce.com/EN/libraries.php',
	package_dir = { '': 'Sources' },
	package_data = { '': ['cdll/*'] },
	packages = [''])
