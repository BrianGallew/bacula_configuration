# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import re
import bacula_tools
import traceback

# Mostly I try to import specific things, but there's something like 200
# constants to be imported here.
from bacula_tools import *

# I know this is poor style, but pyparsing declares a lot of stuff that
# we'll be referencing.
from pyparsing import *

'''Parsing of the configuration files is a lot of work.  Rather than write
my own parser, I'm going to rely heavily on pyparsing to do the heavy
lifting here.  However, pyparsing doesn't seem to show up in any vendor
distributions.  Considering that this is really a one-time operation at any
given site, all of the parsing-related code goes into this file, which is
NOT imported by default.

Lots of monkeypatching here, so this is undoubtedly fragile in the face of
changes to the various resources.

'''


class StringParseSupport:

    '''Parse a string out into top-level resource items and pass them off to the relevant classes.'''
    RB = '}'
    LB = '{'
    file_re = re.compile(r'\s@(.*)\s+', re.MULTILINE)
    comment_re = re.compile(r'#.*', re.MULTILINE)
    semicolon_re = re.compile(r';', re.MULTILINE)
    blankline_re = re.compile(r'^\s+$', re.MULTILINE)
    monitor_re = re.compile(
        r'^\s*m\s*o\s*n\s*i\s*t\s*o\s*r\s*=\s*yes\s*$', re.MULTILINE | re.I)

    def __init__(self, output):
        '''Initialize the instance variables, and set the output device.  There
        should probably be a default set here.'''
        self.output = output
        self.parse_queue = {}
        self.parsed = []
        self.director_config = False
        self.sd_config = False
        self.fd_config = False
        return

    def file_replacement(self, string):
        ''' Do a quick pass through the string looking for file imports.  If/When
        you find any, replace the file import statement with the contents of
        the file to be imported.  Repeat until there are no more file import statements.'''

        # Strip the comments and blank lines out
        string = self.blankline_re.sub('', self.comment_re.sub('', string))

        # Search for any file import statements
        groups = self.file_re.search(string)

        while groups:           # Iterate through the file imports
            filename = groups.group(1)
            string_without_comments = self.comment_re.sub(
                '', open(filename).read())
            string = string.replace(groups.group(), string_without_comments)
            # re-strip blank lines *after* doing the insert.
            string = self.blankline_re.sub('', string)
            # Look again for import statements
            groups = self.file_re.search(string)
        return string

    def break_into_stanzas(self, string):
        '''Split up the input string into resources, and drop each resource into a
        queue to be individually parsed.  The complication is that there
        are nested {} groups, so we have to do some counting and
        re-assembly so we don't break things up in too fine-grained a manner.

        '''
        parts = string.split(self.RB)

        # Split it up into parts, stored in self.parse_queue
        while parts:
            current = parts.pop(0)
            while current.count(self.RB) < (current.count(self.LB) - 1):
                current += self.RB + parts.pop(0)
            try:
                name, body = current.split(self.LB, 1)
            except:
                self.output(current)
                raise
            name = name.strip().lower()
            # special case the Console here because the client config is stupid
            if self.monitor_re.search(body):
                name = CONSOLE
            self.parse_queue.setdefault(name, []).append(body.strip())
            while parts and parts[0] == '\n':
                del parts[0]
        return

    def analyze_queue(self):
        '''Determine what kind of configuration file this is, as that affects the
        parsing process greatly.'''
        if CATALOG.lower() in self.parse_queue:
            self.director_config = True
        elif DEVICE in self.parse_queue:
            self.sd_config = True
        else:
            self.fd_config = True
        return

    def parse_one_stanza_type(self, key):
        '''Parse all of the stanzas of one type.  e.g. all of the Clients  '''
        if not key in self.parse_queue:
            return
        # Actually parse something
        for body in self.parse_queue[key]:
            try:
                obj = bacula_tools._DISPATCHER[key]()
                self.parsed.append(obj)
                if key == DIRECTOR:
                    result = obj.parse_string(
                        body, self.director_config, self.parsed[0])
                elif key == CONSOLE:
                    result = obj.parse_string(
                        body, self.director_config, self.parsed[0])
                elif key in [CATALOG.lower(), MESSAGES, DEVICE]:
                    result = obj.parse_string(body, self.parsed[0])
                else:
                    result = obj.parse_string(body)
                self.output(result)
            except Exception as e:
                msg = '%s: Unable to handle %s at this time:\n%s' % (
                    key.capitalize(), e, body.strip())
                self.output(msg)
        del self.parse_queue[key]
        return

    def parse_it_all(self, string):
        '''Takes a string resulting from reading in a file, and parse it out.
        Think of this as the driver routing for the entire parsing
        process.

        '''
        string = self.file_replacement(string)

        # It should be observed that this statement causes scripts with
        # embedded semi-colons to break parsing.
        string = self.semicolon_re.sub('\n',  string).replace(
            '\\\n', '').replace('\n\n', '\n')

        # Fills in self.parse_queue
        self.break_into_stanzas(string)
        self.analyze_queue()

        # Actually parse the various parts
        # it turns out to be important to do these in a specific order.
        if self.sd_config:
            self.parse_one_stanza_type(STORAGE)
        if self.fd_config:
            self.parse_one_stanza_type(CLIENT)
        if self.fd_config:
            self.parse_one_stanza_type(FILEDAEMON)
        if self.director_config:
            self.parse_one_stanza_type(DIRECTOR)
        for name in self.parse_queue.keys():
            self.parse_one_stanza_type(name)

        return self.parsed


gr_eq = Literal('=')
gr_stripped_string = quotedString.copy().setParseAction(removeQuotes)
gr_opt_quoted_string = gr_stripped_string | restOfLine
gr_number = Word(nums)
gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword(
    'no', caseless=True).setParseAction(replaceWith('0'))
gr_phrase = Group(
    OneOrMore(gr_stripped_string | Word(alphanums)) + gr_eq + gr_opt_quoted_string)

# a collection of utility functions that will be used with parsing.


def np(words, fn=gr_opt_quoted_string, action=None):
    '''Build a parser for a bunch of equivalent keywords.
    '''
    p = Keyword(words[0], caseless=True).setDebug(
        logging.root.level < logging.INFO)
    for w in words[1:]:
        p = p | Keyword(w, caseless=True).setDebug(
            logging.root.level < logging.INFO)
    p = p + gr_eq + fn
    p.setParseAction(action)
    return p


def handle_ip(*x):
    '''Document this
    '''
    a, b, c = x[2]
    return '  %s = { %s }' % (a, c[0])


def handle_monitor(*x):
    '''Oddly enough, we just throw out the monitor flag when parsing the client
    config.  We'll keep it when we parse the director config, though.

    '''
    pass

# Class-specific parsers.  There are a couple classes that use the default
# parser, or even have an in-class declaration.  Those classes are so
# because their parsing requirements are very lightweight.


def catalog_parse_string(self, string, director):
    '''Parsing for the Catalog resource.
    '''
    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    gr_line = gr_line | np(
        (USER, 'dbuser', 'db user'), action=self._parse_setter(USER))
    gr_line = gr_line | np(
        (PASSWORD, 'dbpassword', 'db password'), action=self._parse_setter(PASSWORD))
    gr_line = gr_line | np(
        PList(DBSOCKET), action=self._parse_setter(DBSOCKET))
    gr_line = gr_line | np(
        PList(DBPORT), gr_number, action=self._parse_setter(DBPORT))
    gr_line = gr_line | np(PList('db name'), action=self._parse_setter(DBNAME))
    gr_line = gr_line | np(
        PList('db address'), action=self._parse_setter(DBADDRESS))
    gr_res = OneOrMore(gr_line)
    result = gr_res.parseString(string, parseAll=True)
    self.set(DIRECTOR_ID, director[ID])
    return 'Catalog: ' + self[NAME]


def client_parse_string(self, string):
    '''Parser for the Client resource.
    '''
    def handle_fdaddr(*x):
        '''Docment this.
        '''
        a, b, c = x[2]
        self.set(FDADDRESSES, '  %s' % '\n  '.join(c))
        return

    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    gr_line = gr_line | np((ADDRESS,), action=self._parse_setter(ADDRESS))
    gr_line = gr_line | np(
        (CATALOG,), action=self._parse_setter(CATALOG_ID, dereference=True))
    # Discard the password here!
    gr_line = gr_line | np((PASSWORD,), action=lambda x: x)
    gr_line = gr_line | np(
        PList('file retention'), action=self._parse_setter(FILERETENTION))
    gr_line = gr_line | np(
        PList('job retention'), action=self._parse_setter(JOBRETENTION))
    gr_line = gr_line | np(
        (PRIORITY,), gr_number, action=self._parse_setter(PRIORITY))
    gr_line = gr_line | np(
        PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
    gr_line = gr_line | np(
        PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
    gr_line = gr_line | np(
        PList('heart beat interval'), action=self._parse_setter(HEARTBEATINTERVAL))
    gr_line = gr_line | np(
        PList('fd address'), action=self._parse_setter(FDADDRESS))
    gr_line = gr_line | np(
        PList('fd source address'), action=self._parse_setter(FDSOURCEADDRESS))
    gr_line = gr_line | np(
        PList('pki key pair'), action=self._parse_setter(PKIKEYPAIR))
    gr_line = gr_line | np(
        PList('pki master key'), action=self._parse_setter(PKIMASTERKEY))
    gr_line = gr_line | np(
        PList('fd port'), gr_number, action=self._parse_setter(FDPORT))
    gr_line = gr_line | np(
        PList('auto prune'), gr_yn, action=self._parse_setter(AUTOPRUNE))
    gr_line = gr_line | np(PList('maximum concurrent jobs'),
                           gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
    gr_line = gr_line | np(
        PList('pki encryption'), gr_yn, action=self._parse_setter(PKIENCRYPTION))
    gr_line = gr_line | np(
        PList('pki signatures'), gr_yn, action=self._parse_setter(PKISIGNATURES))

    # This is a complicated one
    da_addr = np(
        ('Addr', 'Port'), Word(printables), lambda x, y, z: ' '.join(z))
    da_ip = np(('IPv4', 'IPv6', 'IP'), nestedExpr('{', '}', OneOrMore(
        da_addr).setParseAction(lambda x, y, z: ' ; '.join(z)))).setParseAction(handle_ip)
    da_addresses = np(('fd addresses', FDADDRESSES), nestedExpr(
        '{', '}', OneOrMore(da_ip)), handle_fdaddr)

    gr_res = OneOrMore(gr_line | da_addresses)
    result = gr_res.parseString(string, parseAll=True)
    return 'Client: ' + self[NAME]


def console_parse_string(self, string, director_config, obj):
    '''Parser for the Console resource.
    '''

    def handle_password(*x):
        '''Passwords get stuffed into a password store.  I'm not sure how to pull this out.
        '''
        a, b, c = x[2]
        p = PasswordStore(obj, self)
        p.password = c
        p.store()
        return

    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    for key in self.SETUP_KEYS:
        if key == PASSWORD:
            continue
        gr_line = gr_line | np((key,), action=self._parse_setter(key))
    gr_monitor = np((MONITOR,), gr_yn, action=handle_monitor)
    gr_pass = np((PASSWORD,), action=handle_password)

    gr_res = OneOrMore(gr_line | gr_monitor | gr_pass)
    result = gr_res.parseString(string, parseAll=True)
    return 'Console: ' + self[NAME]


def device_parse_string(self, string, obj=None):
    '''Parser for the Device resource.
    '''
    gr_line = np(PList(NAME), action=lambda x: self.set_name(x[2]))
    gr_line = gr_line | np(
        PList('alert command'), action=self._parse_setter(ALERTCOMMAND))
    gr_line = gr_line | np(
        PList('archive device'), action=self._parse_setter(ARCHIVEDEVICE))
    gr_line = gr_line | np(
        PList('changer command'), action=self._parse_setter(CHANGERCOMMAND))
    gr_line = gr_line | np(
        PList('changer device'), action=self._parse_setter(CHANGERDEVICE))
    gr_line = gr_line | np(
        PList('client connect wait'), action=self._parse_setter(CLIENTCONNECTWAIT))
    gr_line = gr_line | np(
        PList('device type'), action=self._parse_setter(DEVICETYPE))
    gr_line = gr_line | np(PList(
        'drive index'), gr_number, action=self._parse_setter(DRIVEINDEX, c_int=True))
    gr_line = gr_line | np(
        PList('maximum block size'), action=self._parse_setter(MAXIMUMBLOCKSIZE))
    gr_line = gr_line | np(
        PList('maximum changer wait'), action=self._parse_setter(MAXIMUMCHANGERWAIT))
    gr_line = gr_line | np(PList('maximum concurrent jobs'), gr_number,
                           action=self._parse_setter(MAXIMUMCONCURRENTJOBS, c_int=True))
    gr_line = gr_line | np(
        PList('maximum file size'), action=self._parse_setter(MAXIMUMFILESIZE))
    gr_line = gr_line | np(
        PList('maximum job spool size'), action=self._parse_setter(MAXIMUMJOBSPOOLSIZE))
    gr_line = gr_line | np(PList(
        'maximum network buffer size'), action=self._parse_setter(MAXIMUMNETWORKBUFFERSIZE))
    gr_line = gr_line | np(
        PList('maximum open wait'), action=self._parse_setter(MAXIMUMOPENWAIT))
    gr_line = gr_line | np(
        PList('maximum part size'), action=self._parse_setter(MAXIMUMPARTSIZE))
    gr_line = gr_line | np(
        PList('maximum rewind wait'), action=self._parse_setter(MAXIMUMREWINDWAIT))
    gr_line = gr_line | np(
        PList('maximum spool size'), action=self._parse_setter(MAXIMUMSPOOLSIZE))
    gr_line = gr_line | np(
        PList('maximum volume size'), action=self._parse_setter(MAXIMUMVOLUMESIZE))
    gr_line = gr_line | np(
        PList('media type'), action=self._parse_setter(MEDIATYPE))
    gr_line = gr_line | np(
        PList('minimum block size'), action=self._parse_setter(MINIMUMBLOCKSIZE))
    gr_line = gr_line | np(
        PList('mount command'), action=self._parse_setter(MOUNTCOMMAND))
    gr_line = gr_line | np(
        PList('mount point'), action=self._parse_setter(MOUNTPOINT))
    gr_line = gr_line | np(
        PList('spool directory'), action=self._parse_setter(SPOOLDIRECTORY))
    gr_line = gr_line | np(
        PList('unmount command'), action=self._parse_setter(UNMOUNTCOMMAND))
    gr_line = gr_line | np(
        PList('volume poll interval'), action=self._parse_setter(VOLUMEPOLLINTERVAL))

    gr_line = gr_line | np(
        PList('always open'), gr_yn, action=self._parse_setter(ALWAYSOPEN))
    gr_line = gr_line | np(
        PList('auto changer'), gr_yn, action=self._parse_setter(AUTOCHANGER))
    gr_line = gr_line | np(
        PList('auto select'), gr_yn, action=self._parse_setter(AUTOSELECT))
    gr_line = gr_line | np(
        PList('automatic mount'), gr_yn, action=self._parse_setter(AUTOMATICMOUNT))
    gr_line = gr_line | np(PList('backward space file'),
                           gr_yn, action=self._parse_setter(BACKWARDSPACEFILE))
    gr_line = gr_line | np(PList('backward space record'),
                           gr_yn, action=self._parse_setter(BACKWARDSPACERECORD))
    gr_line = gr_line | np(
        PList('block check sum'), gr_yn, action=self._parse_setter(BLOCKCHECKSUM))
    gr_line = gr_line | np(
        PList('block positioning'), gr_yn, action=self._parse_setter(BLOCKPOSITIONING))
    gr_line = gr_line | np(
        PList('bsf at eom'), gr_yn, action=self._parse_setter(BSFATEOM))
    gr_line = gr_line | np(
        PList('close on poll'), gr_yn, action=self._parse_setter(CLOSEONPOLL))
    gr_line = gr_line | np(PList('fast forward space file'),
                           gr_yn, action=self._parse_setter(FASTFORWARDSPACEFILE))
    gr_line = gr_line | np(
        PList('forward space file'), gr_yn, action=self._parse_setter(FORWARDSPACEFILE))
    gr_line = gr_line | np(PList(
        'forward space record'), gr_yn, action=self._parse_setter(FORWARDSPACERECORD))
    gr_line = gr_line | np(PList('hardware end of medium'),
                           gr_yn, action=self._parse_setter(HARDWAREENDOFMEDIUM))
    gr_line = gr_line | np(
        PList('label media'), gr_yn, action=self._parse_setter(LABELMEDIA))
    gr_line = gr_line | np(
        PList('offline on unmount'), gr_yn, action=self._parse_setter(OFFLINEONUNMOUNT))
    gr_line = gr_line | np(
        PList('random access'), gr_yn, action=self._parse_setter(RANDOMACCESS))
    gr_line = gr_line | np(
        PList('removable media'), gr_yn, action=self._parse_setter(REMOVABLEMEDIA))
    gr_line = gr_line | np(
        PList('two eof'), gr_yn, action=self._parse_setter(TWOEOF))
    gr_line = gr_line | np(
        PList('use mtiocget'), gr_yn, action=self._parse_setter(USEMTIOCGET))

    gr_res = OneOrMore(gr_line)

    result = gr_res.parseString(string, parseAll=True)
    if obj:
        self.link(obj)
    return 'Device: ' + self[NAME]


def director_parse_string(self, string, director_config, obj):
    '''Parser for the Director resource.
    FTR: this is hideous.
    '''

    def _handle_password(*x):
        a, b, c = x[2]
        a = PasswordStore(obj, self)
        a.password = c
        a.store()
        return

    def _handle_diraddr(*x):
        a, b, c = x[2]
        self.set(DIRADDRESSES, '  %s' % '\n  '.join(c))
        return

    gr_name = np((NAME,), action=lambda x: self.set_name(x[2]))
    gr_address = np((ADDRESS,), action=self._parse_setter(ADDRESS))
    gr_fd_conn = np(PList('fd connect timeout'), gr_number,
                    self._parse_setter(FD_CONNECT_TIMEOUT, True))
    gr_heart = np(PList('heartbeat interval'), gr_number,
                  self._parse_setter(HEARTBEATINTERVAL, True))
    gr_max_con = np(PList('maximum console connections'),
                    gr_number, self._parse_setter(MAXIMUMCONSOLECONNECTIONS, True))
    gr_max_jobs = np(PList('maximum concurrent jobs'), gr_number,
                     action=self._parse_setter(MAXIMUMCONCURRENTJOBS, True))
    gr_pid = np(
        PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
    gr_query = np(PList('query file'), action=self._parse_setter(QUERYFILE))
    gr_scripts = np(
        PList('scripts directory'), action=self._parse_setter(SCRIPTS_DIRECTORY))
    gr_sd_conn = np(PList('sd connect timeout'), gr_number,
                    self._parse_setter(SD_CONNECT_TIMEOUT, True))
    gr_source = np(
        PList('source address'), action=self._parse_setter(SOURCEADDRESS))
    gr_stats = np(
        PList('statistics retention'), action=self._parse_setter(STATISTICS_RETENTION))
    gr_messages = np(
        (MESSAGES,), action=self._parse_setter(MESSAGES_ID, dereference=True))
    gr_work_dir = np(
        PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
    gr_port = np(
        PList('dir port'), gr_number, self._parse_setter(DIRPORT, True))

    # This is a complicated one
    da_addr = np(
        ('Addr', 'Port'), Word(printables), lambda x, y, z: ' '.join(z))
    da_ip = np(('IPv4', 'IPv6', 'IP'), nestedExpr('{', '}', OneOrMore(
        da_addr).setParseAction(lambda x, y, z: ' ; '.join(z)))).setParseAction(handle_ip)
    da_addresses = np(PList('dir addresses'), nestedExpr(
        '{', '}', OneOrMore(da_ip)), _handle_diraddr)

    # if this isn't a director, then we ignore the password
    if director_config:
        gr_pass = np((PASSWORD,), action=self._parse_setter(PASSWORD))
    else:
        gr_pass = np((PASSWORD,), action=_handle_password)

    gr_res = OneOrMore(gr_name | gr_address | gr_fd_conn | gr_heart | gr_max_con | gr_max_jobs | gr_pass | gr_pid |
                       gr_query | gr_scripts | gr_sd_conn | gr_source | gr_stats | gr_messages | gr_work_dir | gr_port | da_addresses)

    result = gr_res.parseString(string, parseAll=True)
    return 'Director: ' + self[NAME]


def fileset_parse_string(self, string):
    '''Parser for the Fileset resource.
    '''
    # why dos this one use lambda x,y, and other parsers only use lambda x?
    gr_name = np((NAME,), action=lambda x, y=self: y.set_name(x[2]))
    gr_ifsc = np(PList('Ignore File Set Changes'), gr_yn,
                 action=self._parse_setter(IGNOREFILESETCHANGES))
    gr_evss = np(
        PList('Enable VSS'), gr_yn, action=self._parse_setter(ENABLEVSS))

    gr_i_option = Group(Keyword(OPTIONS, caseless=True) +
                        nestedExpr('{', '}', Regex('[^\}]+', re.MULTILINE)))
    gr_e_option = gr_i_option.copy()
    gr_i_file = gr_phrase.copy()
    gr_e_file = gr_phrase.copy()

    gr_inc = Keyword('include', caseless=True) + \
        nestedExpr('{', '}', OneOrMore(gr_i_option | gr_i_file))
    gr_inc.addParseAction(self._parse_add_entry)
    gr_exc = Keyword('exclude', caseless=True) + \
        nestedExpr('{', '}', OneOrMore(gr_e_option | gr_e_file))
    gr_exc.addParseAction(self._parse_add_entry)

    gr_res = OneOrMore(gr_name | gr_inc | gr_exc | gr_ifsc | gr_evss)
    result = gr_res.parseString(string, parseAll=True)
    return 'Fileset: ' + self[NAME]


def job_parse_string(self, string):
    '''Parser for the Job resource.
    '''

    # Easy ones that go don't take embedded spaces because I say so.
    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    for key in [TYPE, LEVEL, REPLACE, BASE, RUN, WHERE]:
        gr_line = gr_line | np((key,), action=self._parse_setter(key))

    # Group of _id variables

    gr_line = gr_line | np(
        PList('differential pool'), action=self._parse_setter(DIFFERENTIALPOOL_ID))
    gr_line = gr_line | np(
        PList('file set'), action=self._parse_setter(FILESET_ID, dereference=True))
    gr_line = gr_line | np(
        PList('full pool'), action=self._parse_setter(FULLPOOL_ID))
    gr_line = gr_line | np(
        (CLIENT,), action=self._parse_setter(CLIENT_ID, dereference=True))
    gr_line = gr_line | np(
        PList('incremental pool'), action=self._parse_setter(INCREMENTALPOOL_ID))
    gr_line = gr_line | np(
        (MESSAGES,), action=self._parse_setter(MESSAGES_ID, dereference=True))
    gr_line = gr_line | np(
        (POOL,), action=self._parse_setter(POOL_ID, dereference=True))
    gr_line = gr_line | np(
        (SCHEDULE,), action=self._parse_setter(SCHEDULE_ID, dereference=True))
    gr_line = gr_line | np(
        (STORAGE,), action=self._parse_setter(STORAGE_ID, dereference=True))
    gr_line = gr_line | np(
        PList('job defs'), action=self._parse_setter(JOB_ID, dereference=True))

    # INTs

    gr_line = gr_line | np(PList('maximum concurrent jobs'),
                           gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
    gr_line = gr_line | np(
        PList('re schedule times'), gr_number, action=self._parse_setter(RESCHEDULETIMES))
    gr_line = gr_line | np(
        (PRIORITY,), gr_number, action=self._parse_setter(PRIORITY))

    # True/False

    gr_line = gr_line | np(
        (ACCURATE,), gr_yn, action=self._parse_setter(ACCURATE))
    gr_line = gr_line | np(PList(
        'allow duplicate jobs'), gr_yn, action=self._parse_setter(ALLOWDUPLICATEJOBS))
    gr_line = gr_line | np(PList(
        'allow mixed priority'), gr_yn, action=self._parse_setter(ALLOWMIXEDPRIORITY))
    gr_line = gr_line | np(PList('cancel lower level duplicates'),
                           gr_yn, action=self._parse_setter(CANCELLOWERLEVELDUPLICATES))
    gr_line = gr_line | np(PList('cancel queued duplicates'),
                           gr_yn, action=self._parse_setter(CANCELQUEUEDDUPLICATES))
    gr_line = gr_line | np(PList('cancel running duplicates'),
                           gr_yn, action=self._parse_setter(CANCELRUNNINGDUPLICATES))
    gr_line = gr_line | np(
        (ENABLED,), gr_yn, action=self._parse_setter(ENABLED))
    gr_line = gr_line | np(PList('prefer mounted volumes'),
                           gr_yn, action=self._parse_setter(PREFERMOUNTEDVOLUMES))
    gr_line = gr_line | np(
        PList('prefix links'), gr_yn, action=self._parse_setter(PREFIXLINKS))
    gr_line = gr_line | np(
        PList('prune files'), gr_yn, action=self._parse_setter(PRUNEFILES))
    gr_line = gr_line | np(
        PList('prune jobs'), gr_yn, action=self._parse_setter(PRUNEJOBS))
    gr_line = gr_line | np(
        PList('prune volumes'), gr_yn, action=self._parse_setter(PRUNEVOLUMES))
    gr_line = gr_line | np(PList(
        're run failed levels'), gr_yn, action=self._parse_setter(RERUNFAILEDLEVELS))
    gr_line = gr_line | np(PList(
        're schedule on error'), gr_yn, action=self._parse_setter(RESCHEDULEONERROR))
    gr_line = gr_line | np(
        PList('spool attributes'), gr_yn, action=self._parse_setter(SPOOLATTRIBUTES))
    gr_line = gr_line | np(
        PList('spool data'), gr_yn, action=self._parse_setter(SPOOLDATA))
    gr_line = gr_line | np(
        PList('write boot strap'), gr_yn, action=self._parse_setter(WRITEPARTAFTERJOB))

    # plain strings

    gr_line = gr_line | np((NOTES,), action=self._parse_setter(NOTES))
    gr_line = gr_line | np(
        (ADDPREFIX, 'add prefix'), action=self._parse_setter(ADDPREFIX))
    gr_line = gr_line | np(
        (ADDSUFFIX, 'add suffix'), action=self._parse_setter(ADDSUFFIX))
    gr_line = gr_line | np((BASE,), action=self._parse_setter(BASE))
    gr_line = gr_line | np(
        (BOOTSTRAP, 'boot strap'), action=self._parse_setter(BOOTSTRAP))
    gr_line = gr_line | np((DIFFERENTIALMAXWAITTIME, 'differential max wait time', 'differentialmaxwait time', 'differentialmax waittime', 'differential maxwaittime',
                            'differentialmax wait time', 'differential maxwait time', 'differential max waittime'), action=self._parse_setter(DIFFERENTIALMAXWAITTIME))
    gr_line = gr_line | np(('incremental-differentialmaxwaittime', 'incremental-differential maxwaittime', 'incremental-differentialmax waittime', 'incremental-differentialmaxwait time',
                            'incremental-differential max waittime', 'incremental-differential maxwait time', 'incremental-differentialmax wait time', 'incremental-differential max wait time',), action=self._parse_setter(IDMAXWAITTIME))
    gr_line = gr_line | np((INCREMENTALMAXRUNTIME, 'incremental max run time', 'incrementalmaxrun time', 'incrementalmax runtime', 'incremental maxruntime',
                            'incrementalmax run time', 'incremental maxrun time', 'incremental max runtime'), action=self._parse_setter(INCREMENTALMAXRUNTIME))
    gr_line = gr_line | np((MAXFULLINTERVAL, 'max full interval', 'max fullinterval',
                            'maxfull interval'), action=self._parse_setter(MAXFULLINTERVAL))
    gr_line = gr_line | np((MAXIMUMBANDWIDTH, 'maximum band width', 'maximum bandwidth',
                            'maximumband width'), action=self._parse_setter(MAXIMUMBANDWIDTH))
    gr_line = gr_line | np((MAXRUNSCHEDTIME, 'max run sched time', 'maxrunsched time', 'maxrun schedtime', 'max runschedtime',
                            'maxrun sched time', 'max runsched time', 'max run schedtime'), action=self._parse_setter(MAXRUNSCHEDTIME))
    gr_line = gr_line | np(
        (MAXRUNTIME, 'max run time', 'maxrun time', 'max runtime'), action=self._parse_setter(MAXRUNTIME))
    gr_line = gr_line | np((MAXSTARTDELAY, 'max start delay', 'max startdelay',
                            'maxstart delay'), action=self._parse_setter(MAXSTARTDELAY))
    gr_line = gr_line | np((MAXWAITTIME, 'max wait time', 'max waittime',
                            'maxwait time'), action=self._parse_setter(MAXWAITTIME))
    gr_line = gr_line | np(
        (REGEXWHERE, 'regex where'), action=self._parse_setter(REGEXWHERE))
    gr_line = gr_line | np((RESCHEDULEINTERVAL, 're schedule interval', 're scheduleinterval',
                            'reschedule interval'), action=self._parse_setter(RESCHEDULEINTERVAL))
    gr_line = gr_line | np((RUN,), action=self._parse_setter(RUN))
    gr_line = gr_line | np(
        (SPOOLSIZE, 'spool size'), action=self._parse_setter(SPOOLSIZE))
    gr_line = gr_line | np(
        (STRIPPREFIX, 'strip prefix'), action=self._parse_setter(STRIPPREFIX))
    gr_line = gr_line | np(
        (VERIFYJOB, 'verify job'), action=self._parse_setter(VERIFYJOB))
    gr_line = gr_line | np((WHERE,), action=self._parse_setter(WHERE))
    gr_line = gr_line | np((WRITEBOOTSTRAP, 'write boot strap', 'write bootstrap',
                            'writeboot strap'), action=self._parse_setter(WRITEBOOTSTRAP))

    # The ugliness that is run scripts
    gr_line = gr_line | np(PList('Run Before Job'), gr_stripped_string,
                           action=self._parse_script(runsonclient=0, runswhen='Before'))
    gr_line = gr_line | np(PList('Run After Job'), gr_stripped_string,
                           action=self._parse_script(runsonclient=0, runswhen='After'))
    gr_line = gr_line | np(PList('Run After Failed Job'), gr_stripped_string, action=self._parse_script(runsonsuccess=0, runsonfailure=1,
                                                                                                        runsonclient=0, runswhen='After'))
    gr_line = gr_line | np(PList('Client Run Before Job'),
                           gr_stripped_string, action=self._parse_script(runswhen='Before'))
    gr_line = gr_line | np(PList(
        'Client Run After Job'), gr_stripped_string, action=self._parse_script(runswhen='After'))

    # This is a complicated one
    gr_script_parts = np(
        ('Command',), gr_stripped_string, action=nullDebugAction)
    gr_script_parts = gr_script_parts | np(
        (CONSOLE,), gr_stripped_string, action=nullDebugAction)
    gr_script_parts = gr_script_parts | np(
        PList('Runs When'), action=nullDebugAction)
    gr_script_parts = gr_script_parts | np(
        PList('Runs On Success'), gr_yn, action=nullDebugAction)
    gr_script_parts = gr_script_parts | np(
        PList('Runs On Failure'), gr_yn, action=nullDebugAction)
    gr_script_parts = gr_script_parts | np(
        PList('Runs On Client'), gr_yn, action=nullDebugAction)
    gr_script_parts = gr_script_parts | np(
        PList('Fail Job On Error'), gr_yn, action=nullDebugAction)
    gr_script = ((Keyword('Run Script', caseless=True) | Keyword('RunScript', caseless=True)) +
                 nestedExpr('{', '}', OneOrMore(gr_script_parts))).setParseAction(self._parse_script_full)

    gr_res = OneOrMore(gr_line | gr_script)
    try:
        result = gr_res.parseString(string, parseAll=True)
    except Exception as e:
        print(e)
        raise
    return self.retlabel + ': ' + self[NAME]


def messages_parse_string(self, string, obj=None):
    '''Extend the standard parse_string functionality with object linkage.
    This is the solution I came up with for associating a Message with
    a Director, Client, or Storage object.
    '''
    retval = DbDict.parse_string(self, string)
    if obj:
        self.link(obj)
    return retval


def pool_parse_string(self, string):
    '''Parse a tring into a Pool object.
    '''

    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    gr_line = gr_line | np(
        PList('pool type'), action=self._parse_setter(POOLTYPE))
    gr_line = gr_line | np(
        PList('maximum volumes'), action=self._parse_setter(MAXIMUMVOLUMES))
    gr_line = gr_line | np(
        (STORAGE,), action=self._parse_setter(STORAGE_ID, dereference=True))
    gr_line = gr_line | np(
        PList('use volume once'), gr_yn, action=self._parse_setter(USEVOLUMEONCE))
    gr_line = gr_line | np(
        PList('catalog files'), gr_yn, action=self._parse_setter(CATALOGFILES))
    gr_line = gr_line | np(
        PList('auto prune'), gr_yn, action=self._parse_setter(AUTOPRUNE))
    gr_line = gr_line | np(
        (RECYCLE,), gr_yn, action=self._parse_setter(RECYCLE))
    gr_line = gr_line | np(PList('recycle oldest volume'),
                           gr_yn, action=self._parse_setter(RECYCLEOLDESTVOLUME))
    gr_line = gr_line | np(PList('recycle current volume'),
                           gr_yn, action=self._parse_setter(RECYCLECURRENTVOLUME))
    gr_line = gr_line | np(PList('purge oldest volume'),
                           gr_yn, action=self._parse_setter(PURGEOLDESTVOLUME))
    gr_line = gr_line | np(PList(
        'maximum volume jobs'), gr_number, action=self._parse_setter(MAXIMUMVOLUMEJOBS))
    gr_line = gr_line | np(PList(
        'maximum volume files'), gr_number, action=self._parse_setter(MAXIMUMVOLUMEFILES))
    gr_line = gr_line | np(
        PList('maximum volume bytes'), action=self._parse_setter(MAXIMUMVOLUMEBYTES))
    gr_line = gr_line | np(
        PList('volume use duration'), action=self._parse_setter(VOLUMEUSEDURATION))
    gr_line = gr_line | np(
        PList('volume retention'), action=self._parse_setter(VOLUMERETENTION))
    gr_line = gr_line | np(
        PList('action on purge'), action=self._parse_setter(ACTIONONPURGE))
    gr_line = gr_line | np(
        PList('scratch pool'), action=self._parse_setter(SCRATCHPOOL))
    gr_line = gr_line | np(
        PList('recycle pool'), action=self._parse_setter(RECYCLEPOOL))
    gr_line = gr_line | np(
        PList('file retention'), action=self._parse_setter(FILERETENTION))
    gr_line = gr_line | np(
        PList('job retention'), action=self._parse_setter(JOBRETENTION))
    gr_line = gr_line | np(
        PList('cleaning prefix'), action=self._parse_setter(CLEANINGPREFIX))
    gr_line = gr_line | np(
        PList('label format'), action=self._parse_setter(LABELFORMAT))

    gr_res = OneOrMore(gr_line)
    result = gr_res.parseString(string, parseAll=True)
    return 'Pool: ' + self[NAME]


def schedule_parse_string(self, string):
    '''Parse a string into a Schedule object.

    We're going to make a log of assumption here, not the least of
    which is that what will be passed in is a single Schedule{}
    resource, without comments.  Anything else will throw an
    exception.'''
    run_re = re.compile(r'^\s*run\s*=\s*(.*)', re.MULTILINE | re.IGNORECASE)
    data = string.strip()
    g = self.name_re.search(data).groups()
    s = g[0].strip()
    if s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    if s[0] == "'" and s[-1] == "'":
        s = s[1:-1]
    self.set_name(s)
    data = self.name_re.sub('', data)
    while True:
        g = run_re.search(data)
        if not g:
            break
        s = g.group(1).strip()
        if s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        if s[0] == "'" and s[-1] == "'":
            s = s[1:-1]
        self._add_run(s)
        data = run_re.sub('', data, 1)
    return "Schedule: " + self[NAME]


def storage_parse_string(self, string):
    '''Populate a new Storage from a string.
    '''

    def _handle_addr(*x):
        a, b, c = x[2]
        self.set(SDADDRESSES, '  %s' % '\n  '.join(c))
        return

    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    gr_line = gr_line | np(
        PList('sd port'), gr_number, action=self._parse_setter(SDPORT))
    gr_line = gr_line | np(
        (ADDRESS, 'sd address', SDADDRESS), action=self._parse_setter(ADDRESS))
    gr_line = gr_line | np((PASSWORD,), action=lambda x: x)
    gr_line = gr_line | np((DEVICE,), action=self._parse_setter(DEVICE))
    gr_line = gr_line | np(
        PList('media type'), action=self._parse_setter(MEDIATYPE))
    gr_line = gr_line | np(
        PList('auto changer'), gr_yn, action=self._parse_setter(AUTOCHANGER))
    gr_line = gr_line | np(PList('maximum concurrent jobs'),
                           gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
    gr_line = gr_line | np(
        PList('allow compression'), gr_yn, action=self._parse_setter(ALLOWCOMPRESSION))
    gr_line = gr_line | np(
        PList('heartbeat interval'), action=self._parse_setter(HEARTBEATINTERVAL))

    gr_line = gr_line | np(
        PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
    gr_line = gr_line | np(
        PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
    gr_line = gr_line | np(
        PList('client connect wait'), action=self._parse_setter(CLIENTCONNECTWAIT))

    # This is a complicated one
    da_addr = np(
        ('Addr', 'Port'), Word(printables), lambda x, y, z: ' '.join(z))
    da_ip = np(('IPv4', 'IPv6', 'IP'), nestedExpr('{', '}', OneOrMore(
        da_addr).setParseAction(lambda x, y, z: ' ; '.join(z)))).setParseAction(handle_ip)
    da_addresses = np(PList('sd addresses'), nestedExpr(
        '{', '}', OneOrMore(da_ip)), _handle_addr)

    gr_res = OneOrMore(gr_line)
    result = gr_res.parseString(string, parseAll=True)
    return 'Storage: ' + self[NAME]


def counter_parse_string(self, string):
    '''Parser for the Counter resource.
    '''
    gr_line = np((NAME,), action=lambda x: self.set_name(x[2]))
    gr_line = gr_line | np((MINIMUM,), action=self._parse_setter(MINIMUM))
    gr_line = gr_line | np((MAXIMUM,), action=self._parse_setter(MAXIMUM))
    gr_line = gr_line | np(
        PList('wrap counter'), action=self._parse_setter(COUNTER_ID, dereference=True))
    gr_line = gr_line | np(
        (CATALOG,), action=self._parse_setter(CATALOG_ID, dereference=True))
    gr_res = OneOrMore(gr_line)
    result = gr_res.parseString(string, parseAll=True)
    return 'Counter: ' + self[NAME]


def setup_for_parsing():
    '''Monkeypatch real parsing support into all of the classes that need it.
    These were originally all in the actual class definition, but I pulled
    it out for two reasons:

    1) Puts all of the code that relies on pyparsing into one place (that
    is never loaded without explicitly importing it, and
    2) Reduces a lot of the duplicated boilerplate

    Yes, it makes this file a little unwieldy, but it also means that all
    of the parsing support lives in one place, and that should make it
    worth it to anyone else who has to edit the code.

    '''
    bacula_tools.Catalog.parse_string = catalog_parse_string
    bacula_tools.Client.parse_string = client_parse_string
    bacula_tools.Console.parse_string = console_parse_string
    bacula_tools.Device.parse_string = device_parse_string
    bacula_tools.Director.parse_string = director_parse_string
    bacula_tools.Fileset.parse_string = fileset_parse_string
    bacula_tools.Job.parse_string = job_parse_string
    bacula_tools.Messages.parse_string = messages_parse_string
    bacula_tools.Pool.parse_string = pool_parse_string
    bacula_tools.Schedule.parse_string = schedule_parse_string
    bacula_tools.Storage.parse_string = storage_parse_string
    bacula_tools.Counter.parse_string = counter_parse_string
    pass


def parser(string, output=print):
    '''This is the primary entry point for the parser.  Call it with a string
    and a function to be called for ouput.'''
    setup_for_parsing()
    p = StringParseSupport(output)
    return p.parse_it_all(string)
