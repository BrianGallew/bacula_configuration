'''Bacula configuration database stuff: common routines, credentials, etc.
Configuration is at the *end* of this file.'''

import re, shlex, sys, os


_INTERNED = ['address', 'begin', 'Catalog', 'data', 'db', 'dbaddress',  'dbname', 'dbpassword',
             'hosts', 'dbuser', 'director', 'directors', 'director_name', 'dirid', 'enabled', 'entries',
             'end', 'exclude', 'excludes', 'failure', 'fileset', 'filesets', 'hostid', 'hostname', 'hostnames', 'id',
             'includes', 'lastupdated', 'name', 'no', 'notes', 'os', 'owners', 'password', 'pool', 'option',
             'primary_dir', 'priority', 'rows', 'run', 'schedule', 'schedules', 'schedule_time', 'vssenabled',
             'storagepassword', 'storageserver', 'storageserveraddress', 'timespan', 'yes', 'fileset_files',
             'service', 'services', 'bacula_enabled', 'file_retention', 'job_retention', 'options', 'messages',
             'Full', 'Used', 'Append', 'Cleaning', 'Error', 'Purged', 'Recycle', 'Available', 'ignorechanges',
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
from fileset import Fileset
from messages import Messages

_DISPATCHER = {
    FILESET: Fileset,
    SCHEDULE: Schedule,
    MESSAGES: Messages,
    }
