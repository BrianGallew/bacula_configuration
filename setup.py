#! /usr/bin/env python
import os, glob
from distutils.core import setup

NAME = 'bacula_configuration'
VERSION = '0.1'
WEBSITE = 'http://gallew.org/bacula_configuration'
LICENSE = 'GPLv3 or later'
DESCRIPTION = 'Bacula configuration management tool'
LONG_DESCRIPTION = 'Bacula is a great backup tool, but ships with no way to manage the configuration.  This suite will help you solve the management problem'
AUTHOR = 'Brian Gallew'
EMAIL = 'bacula_configuration@gallew.org'

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=EMAIL,
      url=WEBSITE,
      scripts = glob.glob('bin/*'),
      package_data = {'bacula_configuration': ['data/*']},
      packages=['bacula_configuration',],
      classifiers=['Development Status :: 5 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Utilities'],
      )
