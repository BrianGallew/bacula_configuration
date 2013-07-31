'''Bacula configuration database stuff: common routines, credentials, etc.
Configuration is at the *end* of this file.'''

import re, shlex, sys, os


_INTERNED = ['Append', 'Available', 'Catalog', 'Cleaning', 'Error', 'Full',
             'Purged', 'Recycle', 'Used', 'address', 'bacula_enabled', 'begin',
             'catalogs', 'data', 'db', 'dbaddress', 'dbname', 'dbpassword',
             'dbport', 'dbsocket', 'dbuser', 'diraddresses', 'director',
             'director_name', 'directors', 'dirid', 'enabled', 'end', 'entries',
             'exclude', 'excludes', 'failure', 'fd_connect_timeout', 'file_retention',
             'fileset', 'fileset_files', 'filesets', 'heartbeat_interval', 'hostid',
             'hostname', 'hostnames', 'hosts', 'id', 'ignorechanges', 'includes',
             'job_retention', 'lastupdated', 'maximum_concurrent_jobs',
             'maximumconsoleconnections', 'message_id', 'messages', 'name', 'no',
             'notes', 'option', 'options', 'os', 'owners', 'password', 'pid_directory',
             'pool', 'port', 'primary_dir', 'priority', 'queryfile', 'rows', 'run',
             'schedule', 'schedule_time', 'schedules', 'scripts_directory',
             'sd_connect_timeout', 'service', 'services', 'sourceaddress',
             'statistics_retention', 'storagepassword', 'storageserver',
             'storageserveraddress', 'timespan', 'verid', 'vssenabled',
             'working_directory', 'yes',
             ]

for w in _INTERNED: locals()[w.upper()] = w

STATUS = [FULL, USED, APPEND, CLEANING, ERROR, PURGED, RECYCLE, AVAILABLE]

# Bacula CONFIG DB bits that are less easily interned
BACULA_DIR_PORT = 9101
BACULA_FD_PORT = 9102
BACULA_SD_PORT = 9103
DEBUG = None

WORKING_DIR = {
    'Linux': "/var/lib/bacula",
    'OSX': "/var/db/bacula",
    'FreeBSD': "/var/db/bacula",
    'Windows': "/bacula/working",
    }

def parser(string):
    '''parse a string out into top-level resource items and pass them off to the relevant classes.'''
    # strip out comments, and turn semi-colons into newlines
    # NB: if you have embedded semi-colons in any values (e.g. runscripts),
    # You will lose here.
    RB = '}'
    LB = '{'
    comment_re = re.compile(r'#.*', re.MULTILINE)
    semicolon_re = re.compile(r';', re.MULTILINE)
    string = semicolon_re.sub('\n', comment_re.sub('', string)).replace('\\\n','').replace('\n\n', '\n')
    parts = string.split(RB)
    parsed = []
    while parts:
        current = parts.pop(0)
        while current.count(RB) < (current.count(LB) - 1): current += RB + parts.pop(0)
        name, body = current.split(LB,1)
        name = name.strip().lower()
        try: parsed.append(_DISPATCHER[name](string=body.strip()))
        except Exception, e:
            print 'Unable to handle %s at this time' % name, e
        while parts and parts[0] == '\n': del parts[0]
    return parsed

    

def debug_print(msg, *args):
    global DEBUG
    if DEBUG: print >> sys.stderr, msg % args
    sys.stderr.flush()
    return

def set_debug(value):
    global DEBUG
    DEBUG = value
    return

def set_bool_values(key, value, obj, okey):
    if value in ['1','y','yes','Y','YES','Yes','t','T','true','True','TRUE']:
        if 1 ^ obj[okey]: obj._set(okey, 1)
        return 
    if value in ['0','n','no','N','NO','No','f','F','false','False','FALSE']:
        if 0 ^ obj[okey]: obj._set(okey, 0)
        return
    raise Exception('%s takes a boolean value, and I was unable to translate %s' % (key, value))

# Configuration block

# MySQL credentials for the Bacula configuration database. They should be
# overridden in one of the configuration files (see below for the config
# files that are checked).
MYSQL_DB = 'OVERRIDE ME'
MYSQL_HOST = 'OVERRIDE ME'
MYSQL_USER = 'OVERRIDE ME'
MYSQL_PASS = 'OVERRIDE ME'

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
    exec( open(filename).read(), locals(), locals())

from bacula_config import *
from util import *
from schedule import Schedule
from fileset import Fileset
from messages import Messages
from director import Director
from catalog import Catalog

_DISPATCHER = {
    FILESET: Fileset,
    SCHEDULE: Schedule,
    MESSAGES: Messages,
    DIRECTOR: Director,
    CATALOG.lower(): Catalog,
    }
