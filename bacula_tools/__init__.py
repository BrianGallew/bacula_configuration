# -*- coding: utf-8 -*-

'''Bacula configuration database stuff: common routines, credentials, etc.
Configuration is at the *end* of this file.'''

from __future__ import print_function, absolute_import
import re
import sys
import os
import logging

logging.basicConfig(level=logging.WARNING)

# This is required because of the way I do interning.
# pylint: disable=undefined-variable

# Bacula CONFIG DB bits that are less easily interned
BACULA_DIR_PORT = 9101
BACULA_FD_PORT = 9102
BACULA_SD_PORT = 9103

# Configuration files
BACULA_DIR_CONF = '/etc/bacula/bacula-dir.conf'
BACULA_FD_CONF = '/etc/bacula/bacula-fd.conf'
BACULA_SD_CONF = '/etc/bacula/bacula-sd.conf'
BCONSOLE_CONF = '/etc/bacula/bconsole.conf'

# MySQL credentials for the Bacula configuration database. They should be
# overridden in one of the configuration files (see below for the config
# files that are checked).
MYSQL_DB = 'OVERRIDE ME'
MYSQL_HOST = 'OVERRIDE ME'
MYSQL_USER = 'OVERRIDE ME'
MYSQL_PASS = 'OVERRIDE ME'

_INTERNED = ['Append', 'Available', 'Catalog', 'Cleaning', 'Error',
             'Full', 'Purged', 'Recycle', 'Used', 'actiononpurge', 'addprefix',
             'address', 'addsuffix', 'alertcommand', 'allowcompression',
             'allowmixedpriority', 'alwaysopen', 'archivedevice', 'autochanger',
             'automaticmount', 'autoprune', 'autoprune', 'autoselect',
             'backwardspacefile', 'backwardspacerecord', 'bacula_enabled', 'base',
             'bconsole', 'begin', 'blockchecksum', 'blockpositioning', 'bootstrap',
             'bsfateom', 'cancellowerlevelduplicates', 'cancelqueuedduplicates',
             'cancelrunningduplicates', 'catalog_id', 'catalogacl', 'catalogfiles',
             'catalogs', 'changercommand', 'changerdevice', 'cleaningprefix',
             'client', 'client_id', 'clientacl', 'clientconnectwait',
             'clientconnectwait', 'clients', 'closeonpoll', 'command', 'commandacl',
             'console', 'consoles', 'counter', 'counter_id', 'counters', 'data',
             'db', 'dbaddress', 'dbname', 'dbpassword', 'dbport', 'dbsocket',
             'dbuser', 'device', 'devicetype', 'differentialmaxwaittime',
             'differentialpool_id', 'diraddresses', 'director', 'director_id',
             'director_name', 'directors', 'dirid', 'dirport', 'driveindex',
             'enabled', 'enablevss', 'end', 'entries', 'exclude', 'excludes',
             'failjobonerror', 'failure', 'fastforwardspacefile', 'fd',
             'fd_connect_timeout', 'fdaddress', 'fdaddresses', 'fdport',
             'fdsourceaddress', 'file_retention', 'filedaemon', 'fileretention',
             'fileset', 'fileset_files', 'fileset_id', 'filesetacl', 'filesets',
             'forwardspacefile', 'forwardspacerecord', 'fullpool_id', 'generate',
             'hardwareendofmedium', 'heartbeatinterval', 'hostid', 'hostname',
             'hostnames', 'hosts', 'id', 'idmaxwaittime', 'ignorefilesetchanges',
             'includes', 'incrementalmaxruntime', 'incrementalpool_id', 'job',
             'job_id', 'job_retention', 'jobacl', 'jobdef', 'jobdefs',
             'jobretention', 'jobs', 'labelformat', 'labelmedia', 'lastupdated',
             'level', 'maxfullinterval', 'maximum', 'maximumbandwidth',
             'maximumbandwidthperjob', 'maximumblocksize', 'maximumchangerwait',
             'maximumconcurrentjobs', 'maximumconcurrentjobs',
             'maximumconsoleconnections', 'maximumconsoleconnections',
             'maximumfilesize', 'maximumjobspoolsize', 'maximumnetworkbuffersize',
             'maximumnetworkbuffersize', 'maximumopenwait', 'maximumpartsize',
             'maximumrewindwait', 'maximumspoolsize', 'maximumvolumebytes',
             'maximumvolumefiles', 'maximumvolumejobs', 'maximumvolumes',
             'maximumvolumesize', 'maxrunschedtime', 'maxruntime', 'maxstartdelay',
             'maxwaittime', 'mediatype', 'message', 'messages', 'messages_id',
             'minimum', 'minimumblocksize', 'monitor', 'mountcommand', 'mountpoint',
             'name', 'no', 'notes', 'offlineonunmount', 'option', 'options', 'os',
             'owners', 'password', 'piddirectory', 'pkiencryption', 'pkikeypair',
             'pkimasterkey', 'pkisignatures', 'pool', 'pool_id', 'poolacl', 'pools',
             'pooltype', 'port', 'prefermountedvolumes', 'prefixlinks',
             'primary_dir', 'priority', 'prunefiles', 'prunejobs', 'prunevolumes',
             'purgeoldestvolume', 'queryfile', 'randomaccess', 'recycle',
             'recyclecurrentvolume', 'recycleoldestvolume', 'recyclepool',
             'regexwhere', 'removablemedia', 'replace', 'rerunfailedlevels',
             'rescheduleinterval', 'rescheduleonerror', 'rescheduletimes',
             'accurate', 'allowduplicatejobs', 'rows', 'run', 'runsonclient',
             'runsonfailure', 'runsonsuccess', 'runswhen', 'schedule',
             'schedule_id', 'schedule_time', 'scheduleacl', 'schedules',
             'scratchpool', 'script_id', 'scripts', 'scripts_directory', 'sd',
             'sd_connect_timeout', 'sdaddress', 'sdaddresses', 'sdconnecttimeout',
             'sdport', 'service', 'services', 'sourceaddress', 'spoolattributes',
             'spooldata', 'spooldirectory', 'spoolsize', 'statistics_retention',
             'storage', 'storage_id', 'storageacl', 'storagepassword',
             'storageserver', 'storageserveraddress', 'stripprefix', 'timespan',
             'twoeof', 'type', 'unmountcommand', 'usemtiocget', 'user',
             'usevolumeonce', 'verid', 'verifyjob', 'volumepollinterval',
             'volumeretention', 'volumeuseduration', 'where', 'whereacl',
             'workingdirectory', 'writebootstrap', 'writepartafterjob', 'yes']

for w in _INTERNED:
    locals()[w.upper()] = w

STATUS = [FULL, USED, APPEND, CLEANING, ERROR, PURGED, RECYCLE, AVAILABLE]
TRUE_VALUES = ['1', 'yes', 'y', 'on', 'true', 't']
FALSE_VALUES = ['0', 'no', 'n', 'off', 'false', 'f']

WORKING_DIR = {
    'Linux': "/var/lib/bacula",
    'OSX': "/var/db/bacula",
    'FreeBSD': "/var/db/bacula",
    'Windows': "/bacula/working",
}


def set_debug():
    '''Turn on debug logging'''
    logging.root.setLevel(logging.DEBUG)
    logging.debug('debugging enabled')
    return

# These rules will be used to determine what fileset(s) and schedule(s)
# will be applied to new jobs that are generated in an automated fashion.
# Currently only used by webconfig.  Only HOSTNAME and OS are currently
# valid values.

# The rules in here are examples only!

# [variable, regex, fileset, schedule]
guessing_rules = [
    (HOSTNAME, re.compile('.*origin.*'), 'SetOnHostGZIP', 'CustomHost'),
    (HOSTNAME, re.compile('.*origin.*'), 'XferLogs', 'FtpHosts'),
    (HOSTNAME, re.compile(r'.*\.ocs\..*'), 'SetOnHostGZIP', 'Weekly'),
    (OS, re.compile(r'Windows'), 'WinFullGZIP', 'Weekly'),
]
default_rules = [('Daily', 'FullUnixGZIP')]

# Where we keep
BACULADATADIR = '/data/bacula'


# Now that we've set all of the default initial values, we'll load and
# parse config files, updating the environment from them.  NB: every one of
# these files, if they exist, will be parsed, in this order.  That means
# later files will override earlier ones.
CUSTOM_LIST = ['/etc/bacula/bacula.conf',
               '/usr/local/etc/bacula/bacula.conf',
               '/usr/local/etc/bacula.conf',
               os.path.join(os.environ.get('HOME', '/'), '.bacula.conf'),
               os.environ.get('BACULA_CONF', '/dev/null')
               ]

for filename in CUSTOM_LIST:
    if not os.access(filename, os.R_OK):
        continue
    exec(open(filename).read(), locals(), locals())

from .bacula_config import *
from .util import *
from .schedule import Schedule
from .fileset import Fileset
from .messages import Messages
from .director import Director
from .catalog import Catalog
from .console import Console
from .client import Client
from .pool import Pool
from .storage import Storage
from .job import Job, JobDef
from .scripts import Script
from .device import Device
from .counter import Counter

# bconsole/daemon bits
from .fd import FDaemon
from .sd import SDaemon
from .bacula_director import BDirector


_DISPATCHER = {
    FILESET: Fileset,
    SCHEDULE: Schedule,
    MESSAGES: Messages,
    MESSAGE: Messages,
    DIRECTOR: Director,
    CATALOG.lower(): Catalog,
    CONSOLE: Console,
    CLIENT: Client,
    FILEDAEMON: Client,
    POOL: Pool,
    STORAGE: Storage,
    JOB: Job,
    JOBDEF: JobDef,
    JOBDEFS: JobDef,
    DEVICE: Device,
    COUNTER: Counter,
}
