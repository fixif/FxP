

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
	long_description = f.read()


setup(
	name='FiXiF.FxP',
	version='0.2',
	description='FxP arithmetic library for the FiXiF project',
	long_description=long_description,
	url='https://github.com/FiXiF/FxP',
	author='T. Hilaire, B. Lopez',
	author_email='thibault.hilaire@lip6.fr',
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Science/Research',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Topic :: Scientific/Engineering',
		'Topic :: Software Development :: Embedded Systems',
		'Topic :: Software Development :: Code Generators',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
	],
	keywords='fixed-point arithmetic',
	packages=find_packages(exclude=['tests']),
	install_requires=['mpmath', 'pytest'],
	project_urls={
		'Bug Reports': 'https://github.com/FiXiF/FxP/issues',
		'Source': 'https://github.com/FiXiF/FxP/',
	},
)
