#! /usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

import os
import glob
from setuptools import setup, find_packages

NAME = 'bacula_configuration'
VERSION = '0.94'
WEBSITE = 'http://gallew.org/bacula_configuration'
LICENSE = 'GPLv3 or later'
DESCRIPTION = 'Bacula configuration management tool'
AUTHOR = 'Brian Gallew'
EMAIL = 'bacula_configuration@gallew.org'

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=open('README.md').read(),
      author=AUTHOR,
      author_email=EMAIL,
      url=WEBSITE,
      install_requires=['mysql-python'],
      extras_require={'parsing': ['pyparsing']},
      scripts=glob.glob('bin/*'),
      include_package_data=True,
      zip_safe=False,
      package_data={
          'bacula_tools': ['data/*'],
      },
      packages=['bacula_tools', ],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: System Administrators',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Topic :: Utilities'],
      entry_points={
          'console_scripts': [
              'manage_clients = bacula_tools.client:main',
              'manage_catalogs = bacula_tools.catalog:main',
              'manage_devices = bacula_tools.device:main',
              'manage_filesets = bacula_tools.fileset:main',
              'manage_pools = bacula_tools.pool:main',
              'manage_storage = bacula_tools.storage:main',
              'manage_messages = bacula_tools.messages:main',
              'manage_schedules = bacula_tools.schedule:main',
              'manage_jobs = bacula_tools.job:main',
              'manage_directors = bacula_tools.director:main',
              'manage_scripts = bacula_tools.scripts:main',
          ]
      },
      )
