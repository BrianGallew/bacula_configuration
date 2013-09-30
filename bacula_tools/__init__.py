'''Bacula configuration database stuff: common routines, credentials, etc.
Configuration is at the *end* of this file.'''

from __future__ import print_function
import re, shlex, sys, os

# Just a placeholder, it gets overridden later
DEBUG=False

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

_INTERNED = [
    'Append', 'Available', 'Catalog', 'Cleaning', 'Error', 'Full', 'Purged', 'Recycle', 'Used',
    'actiononpurge', 'address', 'autoprune', 'autoprune', 'bacula_enabled', 'begin', 'catalog_id',
    'catalogacl', 'catalogfiles', 'catalogs', 'cleaningprefix', 'client', 'clientacl', 'clients',
    'commandacl', 'console', 'consoles', 'data', 'db', 'dbaddress', 'dbname', 'dbpassword',
    'dbport', 'dbsocket', 'dbuser', 'diraddresses', 'director', 'director_id', 'director_name',
    'directors', 'dirid', 'enabled', 'end', 'entries', 'exclude', 'excludes', 'failure',
    'fd_connect_timeout', 'fdaddress', 'fdaddresses', 'fdport', 'fdsourceaddress', 'file_retention',
    'filedaemon', 'fileretention', 'fileset', 'fileset_files', 'filesetacl', 'filesets',
    'heartbeatinterval', 'hostid', 'hostname', 'hostnames', 'hosts', 'id',
    'ignorechanges', 'includes', 'job_retention', 'jobacl', 'jobretention', 'labelformat',
    'lastupdated', 'maximumconcurrentjobs', 'maximumbandwidthperjob', 'maximumconcurrentjobs',
    'maximumconsoleconnections', 'maximumconsoleconnections', 'maximumnetworkbuffersize',
    'maximumvolumebytes', 'maximumvolumefiles', 'maximumvolumejobs', 'maximumvolumes', 'messages_id',
    'messages', 'monitor', 'name', 'no', 'notes', 'option', 'options', 'os', 'owners', 'password',
    'piddirectory', 'pkiencryption', 'pkikeypair', 'pkimasterkey', 'pkisignatures', 'pool',
    'poolacl', 'pools', 'pooltype', 'port', 'primary_dir', 'priority', 'purgeoldestvolume',
    'queryfile', 'recycle', 'recyclecurrentvolume', 'recycleoldestvolume', 'recyclepool', 'rows',
    'run', 'schedule', 'schedule_time', 'scheduleacl', 'schedules', 'scratchpool', 'sdport',
    'scripts_directory', 'sd_connect_timeout', 'sdconnecttimeout', 'service', 'services',
    'sourceaddress', 'statistics_retention', 'storage', 'storageacl', 'storagepassword',
    'storageserver', 'storageserveraddress', 'timespan', 'user', 'usevolumeonce', 'verid',
    'volumeretention', 'volumeuseduration', 'vssenabled', 'whereacl', 'workingdirectory', 'yes',
    'device', 'mediatype', 'autochanger', 'allowcompression', 'type', 'level', 'differentialpool_id',
    'fileset_id', 'fullpool_id', 'incrementalpool_id', 'client_id', 'pool_id',
    'schedule_id', 'job_id', 'rescheduletimes', 'accurate', 'allowduplicatejobs',
    'allowmixedpriority', 'cancellowerlevelduplicates', 'cancelqueuedduplicates',
    'cancelrunningduplicates', 'prefermountedvolumes', 'prefixlinks', 'prunefiles', 'prunejobs',
    'prunevolumes', 'rerunfailedlevels', 'rescheduleonerror', 'spoolattributes', 'spooldata',
    'writepartafterjob', 'addprefix', 'addsuffix', 'base', 'bootstrap', 'differentialmaxwaittime',
    'idmaxwaittime', 'incrementalmaxruntime', 'maxfullinterval', 'maximumbandwidth',
    'maxrunschedtime', 'maxruntime', 'maxstartdelay', 'maxwaittime', 'regexwhere',
    'rescheduleinterval', 'spoolsize', 'stripprefix', 'verifyjob', 'where', 'writebootstrap',
    'replace', 'jobdef', 'jobs', 'job', 'storage_id', 'command', 'runsonsuccess', 'runsonfailure',
    'runsonclient', 'runswhen', 'failjobonerror', 'scripts', 'message', 'script_id', 'jobdefs',
    'clientconnectwait', 'sdaddresses', 'sdaddress',

    'archivedevice', 'devicetype', 'changerdevice', 'changercommand', 'alertcommand',
    'driveindex', 'maximumchangerwait', 'maximumrewindwait',
    'maximumopenwait', 'volumepollinterval', 'mountpoint', 'mountcommand', 'unmountcommand',
    'minimumblocksize', 'maximumblocksize', 'maximumvolumesize', 'maximumfilesize',
    'maximumnetworkbuffersize', 'maximumspoolsize', 'maximumjobspoolsize', 'spooldirectory',
    'maximumpartsize', 'autoselect', 'alwaysopen', 'closeonpoll', 'removablemedia',
    'randomaccess', 'blockchecksum', 'hardwareendofmedium', 'fastforwardspacefile', 'usemtiocget',
    'bsfateom', 'twoeof', 'backwardspacerecord', 'backwardspacefile', 'forwardspacerecord',
    'forwardspacefile', 'offlineonunmount', 'blockpositioning', 'labelmedia', 'automaticmount',
    'clientconnectwait','fd','sd', 'bconsole'
    ]

for w in _INTERNED: locals()[w.upper()] = w

STATUS = [FULL, USED, APPEND, CLEANING, ERROR, PURGED, RECYCLE, AVAILABLE]

WORKING_DIR = {
    'Linux': "/var/lib/bacula",
    'OSX': "/var/db/bacula",
    'FreeBSD': "/var/db/bacula",
    'Windows': "/bacula/working",
    }

def parser(string, output=print):
    '''parse a string out into top-level resource items and pass them off to the relevant classes.'''
    # strip out comments, and turn semi-colons into newlines
    # NB: if you have embedded semi-colons in any values (e.g. runscripts),
    # You will lose here.
    RB = '}'
    LB = '{'
    file_re = re.compile(r'\s@(.*)\s+', re.MULTILINE)
    comment_re = re.compile(r'#.*', re.MULTILINE)
    semicolon_re = re.compile(r';', re.MULTILINE)
    blankline_re = re.compile(r'^\s+$', re.MULTILINE)
    # Strip the comments  and blank lines out
    string = blankline_re.sub('', comment_re.sub('', string))

    # Do a quick pass through the string looking for file imports.  If/When
    # you find any, replace the file import statement with the contents of
    # the file to be imported.  Repeat until there are no more file import statements.
    groups = file_re.search(string)
    while groups:
        filename = groups.group(1)
        string = blankline_re.sub('', string.replace(groups.group(), comment_re.sub('', open(filename).read())))
        groups = file_re.search(string)

    # It should be observed that this statement causes scripts with
    # embedded semi-colons to break parsing.
    string = semicolon_re.sub('\n',  string).replace('\\\n','').replace('\n\n', '\n')
    
    parts = string.split(RB)
    parse_queue = {}
    parsed = []

    # Split it up into parts
    while parts:
        current = parts.pop(0)
        while current.count(RB) < (current.count(LB) - 1): current += RB + parts.pop(0)
        try: name, body = current.split(LB,1)
        except:
            output(current)
            raise
        name = name.strip().lower()
        parse_queue.setdefault(name, []).append(body.strip())
        while parts and parts[0] == '\n': del parts[0]

    # Determine what kind of config this is.  Right now, we only care if
    # it's a director, but that may change.
    director_config = False
    sd_config = False
    fd_config = False
    if 'catalog' in parse_queue: director_config = True
    elif 'device' in parse_queue: sd_config = True
    else: fd_config = True

    # Actually parse the various parts
    for name in parse_queue.keys():
        for body in parse_queue[name]:
            try:
                obj = _DISPATCHER[name]()
                parsed.append(obj)
                if name == DIRECTOR: result = obj.parse_string(body, director_config)
                else: result = obj.parse_string(body)
                output(result)
            except Exception as e:
                msg = '%s: Unable to handle %s at this time:\n%s' % (name.capitalize(), e,body.strip())
                output(msg)
    if director_config:
        this_director = [x for x in parsed if type(x) == Director][0]
        for x in parsed:
            if type(x) == Catalog: x._set(DIRECTOR_ID, this_director[ID])
    return parsed
    

def debug_print(msg, *args):
    global DEBUG
    if DEBUG: print(msg % args, file=sys.stderr)
    sys.stderr.flush()
    return

def set_debug(value):
    global DEBUG
    DEBUG = value
    return

set_debug(os.environ.get('DEBUG', False))

def set_bool_values(key, value, obj, okey):
    if value in ['1','y','yes','Y','YES','Yes','t','T','true','True','TRUE']:
        if 1 ^ obj[okey]: obj._set(okey, 1)
        return 
    if value in ['0','n','no','N','NO','No','f','F','false','False','FALSE']:
        if 0 ^ obj[okey]: obj._set(okey, 0)
        return
    raise Exception('%s takes a boolean value, and I was unable to translate %s' % (key, value))

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
from console import Console
from client import Client
from pool import Pool
from storage import Storage
from job import Job, JobDef
from scripts import Script
from device import Device

# bconsole/daemon bits
from fd import FDaemon
from sd import SDaemon
from bacula_director import BDirector


import util

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
    }
