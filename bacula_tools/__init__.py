'''Bacula configuration database stuff: common routines, credentials, etc.
Configuration is at the *end* of this file.'''

import re, shlex, sys, os

STATUS = ['Full', 'Used', 'Append', 'Cleaning', 'Error', 'Purged', 'Recycle', 'Available']

# Bacula CONFIG DB bits
ADDRESS = 'address'
BACULA_DIR_PORT = 9101
BACULA_FD_PORT = 9102
BACULA_SD_PORT = 9103
BACULAENABLED = 'bacula_enabled'
BEGIN = 'begin'
CATALOG = 'Catalog'
DATA = 'data'
DB = 'db'
DBADDRESS = 'dbaddress'
DBNAME = 'dbname'
DBPASSWORD = 'dbpassword'
DBTABLE = 'hosts'
DBUSER = 'dbuser'
DEBUG = None
DIRECTOR = 'director'
DIRECTORS = 'directors'
DIRECTOR_NAME = 'director_name'
DIRID = 'dirid'
ENABLED = 'enabled'
END = 'end'
FAILURE = 'failure'
FILERETENTION = 'file_retention'
FILESET = 'fileset'
HOSTID = 'hostid'
HOSTNAME = 'hostname'
HOSTNAMES = 'hostnames'
ID = 'id'
JOBRETENTION = 'job_retention'
LASTUPDATED = 'lastupdated'
NAME = 'name'
NO = 'no'
NOTES = 'notes'
OS = 'os'
OWNERS = 'owners'
PASSWORD = 'password'
POOL = 'pool'
PRIMARY_DIR = 'primary_dir'
PRIORITY = 'priority'
ROWS = 'rows'
RUN = 'run'
SCHEDULE = 'schedule'
SCHEDULES = 'schedules'
SCHEDULE_TIME = 'schedule_time'
SERVICE = 'services'
STORAGEPASSWORD = 'storagepassword'
STORAGESERVER = 'storageserver'
STORAGESERVERADDRESS = 'storageserveraddress'
TIMESPAN = 'timespan'
YES = 'yes'
WORKING_DIR = {
    'Linux': "/var/lib/bacula",
    'OSX': "/var/db/bacula",
    'FreeBSD': "/var/db/bacula",
    'Windows': "/bacula/working",
    }


def debug_print(msg, *args):
    global DEBUG
    if DEBUG: print >> sys.stderr, msg % args
    sys.stderr.flush()
    return

def set_debug(value):
    global DEBUG
    DEBUG = value
    return

# Configuration block

# MySQL credentials for the Bacula configuration database
MYSQL_DB = 'baculacfg'
MYSQL_HOST = 'localhost'
MYSQL_USER = 'baculacfg_user'
MYSQL_PASS = 'baculacfg_pass'

# These rules will be used to determine what fileset(s) and schedule(s)
# will be applied to new jobs that are generated in an automated fashion.
# Currently only used by webconfig.  Only HOSTNAME and OS are currently
# valid values.

# The rules in here are examples only!

# [variable, regex, fileset, schedule]
_guessing_rules = [
    (HOSTNAME, re.compile('origin'), 'SetOnHostGZIP', 'CustomHost'),
    (HOSTNAME, re.compile('origin'), 'XferLogs', 'FtpHosts'),
    (HOSTNAME, re.compile(r'\.ocs\.'), 'SetOnHostGZIP', 'Weekly'),
    (OS, re.compile(r'Windows'), 'WinFullGZIP', 'Weekly'),
    ]
_default_rules = [('Daily', 'FullUnixGZIP')]

# Where we keep
BACULADATADIR = '/data/bacula'


# Now that we've set all of the default initial values, we'll load and
# parse config files, updating the environment from them.
CUSTOM_LIST = ['/etc/bacula/bacula.conf',
               '/usr/local/etc/bacula/bacula.conf',
               '/usr/local/etc/bacula.conf',
               os.path.join(os.environ['HOME'], '.bacula.conf')
               ]
for filename in CUSTOM_LIST:
    if not os.access(filename, os.R_OK): continue
    for pair in shlex.split(open(filename), True):
        parts = pair.split('=',1) # Only two pieces!
        if len(parts) != 2:
            print 'Unknown configuration line:', pair
            continue
        try: locals()[parts[0]] = int(parts[1])
        except: locals()[parts[0]] = parts[1]

from bacula_config import *
from util import *
from schedule import Schedule
