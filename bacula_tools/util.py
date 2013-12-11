from __future__ import print_function
try: from . import *
except: from bacula_tools import *
import bacula_tools
import re, os, sys, filecmp, optparse, random

# Extra stuff needed for the console/daemon tools
import socket, hmac, base64, hashlib, time
from random import randint
from struct import pack, unpack

# {{{ guess_os():

os_bits = {
    'bsd': 'FreeBSD',
    'BSD': 'FreeBSD',
    'Macintosh': 'OSX',
    'OS X': 'OSX',
    'apple-darwin': 'OSX',
    'msie': 'Windows',
    'MSIE': 'Windows',
    }

def guess_os():
    '''This is a "futures" item to support a not-yet-written CGI.  Knowing the
    OS will, in turn, possibly give you information on where various
    directories default.'''
    agent = os.environ.get('HTTP_USER_AGENT', '')
    environ = os.environ.get('PATH_INFO','')
    for k in os_bits.keys():
        if k in agent or k in environ:
            return os_bits[k]
    return 'Linux'              # Default

# }}}
# {{{ generate_password():

def generate_password(length=44):
    '''Genearte a new password.'''
    possible = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
    return ''.join(random.choice(possible) for _ in xrange(length))

# }}}
# {{{ guess_schedule_and_filesets(hostname, os):

def guess_schedule_and_filesets(hostname, os):
    '''Another "futures" function to support a CGI.  When a host registers
    itself, you may want to have automatic selection of appropriate scheduls
    and filesets.'''
    results = []
    for (variable, matcher, fileset, schedule) in _guessing_rules:
        if matcher.match(locals()[variable]): results.append((fileset, schedule))
    return results or _default_rules

# }}}
# {{{ die(*msg):

def die(*msg):
    '''Print out error messages and exit.'''
    print("An error occurred and %s is no longer able to continue\n" % sys.argv[0])
    print('\n'.join(msg))
    print('\n')
    exit(-1)
    return                  # This will never happen, but it makes auto-formatting a little happier.

# }}}
def hostname_mangler(fqdn, target=CLIENT):
    '''Alters the hostname in the desired manner to return a client, director,
    or storage name.  You will probably want to OVERRIDE THIS to meet the
    needs of your own site.

    This default function just truncates the last one or two parts of the
    FQDN, regardless of the target type.  As an alternative, the "standard"
    that is used by the Bacula installation scripts is to append "-fd",
    "-sd", or "-dir" to the shortname.  Redefine this function in the
    config file.

    '''
    parts = fqdn.split('.')
    if parts[-1] in ['com', 'org']: del parts[-2:]
    if parts[-1] == 'local': del parts[-1]
    return '.'.join(parts)

def default_jobs(client):
    '''Returns the best guess as to jobs for a newly configured host.  You
    will probably want to OVERRIDE THIS to meet the needs of your own site.

    The default setting here will create a single job named
    client-fileset-schedule, and assumes these exist:
    	Fileset "FullUnix"
    	Schedule "Daily"
    	Messages "Standard"
    	Pool "Default"
    	Storage "File"

    Absent any of those objects, this will fail.
    '''
    message = bacula_tools.Messages({bacula_tools.NAME: 'Standard'}).search()
    pool = bacula_tools.Pool({bacula_tools.NAME: 'Default'}).search()
    storage = bacula_tools.Storage({bacula_tools.NAME: 'File'}).search()
    schedule = bacula_tools.Schedule({bacula_tools.NAME: 'Daily'}).search()
    fileset = bacula_tools.Fileset({bacula_tools.NAME: 'FullUnix'}).search()
    job = bacula_tools.Job({bacula_tools.NAME: '%s-FullUnix-Daily' % client[bacula_tools.NAME],
                            bacula_tools.MESSAGES_ID: message[bacula_tools.ID],
                            bacula_tools.POOL_ID: pool[bacula_tools.ID],
                            bacula_tools.STORAGE_ID: storage[bacula_tools.ID],
                            bacula_tools.SCHEDULE_ID: schedule[bacula_tools.ID],
                            bacula_tools.FILESET_ID: fileset[bacula_tools.ID],
                            bacula_tools.MAXIMUMCONCURRENTJOBS: 1,
                            bacula_tools.PRIORITY: 10,
                            bacula_tools.LEVEL: 'Incremental',
                            bacula_tools.RESCHEDULETIMES: 0,
                            bacula_tools.TYPE: 'Backup',
                            bacula_tools.WRITEBOOTSTRAP: '/var/tmp/%c.bsr',
           })
    job._save()
    # Going to cheat here, as a newly-created client won't have any
    # Messages associated.
    message.link(client)
    return 

def default_director(client, dname=''):
    '''Selects a director (preferring the value passed in if possible), and
    creates a new password for use with that director.  You will
    undoubtedly want to OVERRIDE THIS to meet the needs of your own
    site.  The default in this case is the first one returned by a select
    against the director table with no where clause.'''
    if not dname:
        bc = bacula_tools.Bacula_Factory()
        dname =  bc.do_sql('SELECT name FROM %s LIMIT 1' % bacula_tools.Director.table)[0]

    d = bacula_tools.Director().search(dname)
    password = bacula_tools.PasswordStore(client[ID], d[ID])
    password.password = bacula_tools.GENERATE
    password.store()

    
    
class ConfigFile(object):
    '''Easy config file management wrapper.

    This will give you a file-like object that can be easily used to write
    out various bits of output.  If the new output differs from the current
    contents of the target configuration file, upon close this will
    overwrite the destination file and return True.  This, in turn, can let
    you drive processes like "restart bacula-sd if the config file
    changes".

    '''
    FILEHEADER = "# This config file generated by %s script.\n#\n#DO NOT EDIT THIS FILE BY HAND\n\n" % sys.argv[0]
    # {{{ __init__(filename)    # file to update (or not, as the case may be)

    def __init__(self, filename):
        self.filename = filename
        self.newfilename = filename + '.new'
        self.fh = open(self.newfilename, 'w')
        self.fh.write(self.FILEHEADER)
        debug_print("Opened %s", self.newfilename)
        return

    # }}}
    # {{{ close(*data):              # Returns True if an actual update happens

    def close(self, *data):
        '''Write out the data.  Compare that with the target destination file and
        overwrite if necessary.'''
        if data: self.write(*data)
        self.fh.flush()
        self.fh.close()
        try: test_value = filecmp.cmp(self.filename, self.newfilename)
        except: test_value = False
        if test_value:
            os.unlink(self.newfilename)
            debug_print("\t%s doesn't need to be updated", self.filename)
            return False
        debug_print("\tupdating %s", self.filename)
        os.rename(self.newfilename, self.filename)
        return True

# }}}
    # {{{ write(*data): writes data out to the file, appending newlines for each item passed in

    def write(self, *data):
        '''Write data out, with newlines after each item.'''
        for line in data:
            self.fh.write(str(line))
            self.fh.write('\n')
        return

# }}}

class PasswordStore(object):
    '''Client resources have passwords associated.  This class helps manage
    that.  Instantiate with a Client ID and a Director ID.'''
    bc = bacula_tools.Bacula_Factory()
    column1 = 'client_id'
    table = 'client_pwords'
    _select = 'SELECT * FROM %s where %s = %%s and %s = %%s'
    _insert = 'INSERT INTO %s (%s, director_id, password %s) values (%%s, %%s, %%s %s)'
    _update = 'UPDATE %s set password=%%s %s where %s=%%s and director_id=%%s'
    _delete = 'DELETE FROM %s where %s=%%s and director_id=%%s'
    # {{{ __init__(id1, director_id):

    def __init__(self, id1, director_id):
        self.id = id1
        self.director_id = director_id
        self.load()
        return

        # }}}
    # {{{ load():

    def load(self):
        '''Load data from the database'''
        sql = self._select % (self.table, self.column1, DIRECTOR_ID)
        value = self.bc.do_sql(sql, (self.id, self.director_id), asdict=True)
        if len(value) == 1:
            value = value[0]
            self.password = value[PASSWORD]
            if value.has_key(MONITOR): self.monitor = value[MONITOR]
        return

        # }}}
    # {{{ store():

    def store(self):
        '''Write the data out to the database'''
        if self.password == GENERATE: self.password = generate_password()
        if not self.password:
            sql = self._delete % (self.table, self.column1)
            self.bc.do_sql(sql, (self.id, self.director_id))
            return
        if hasattr(self, MONITOR):
            values = (self.password, self.monitor)
            m = ", monitor=%s"
            n = ', monitor'
            i = ', %s'
        else:
            values = (self.password,)
            m = ""
            n = ""
            i = ''
        try:
            sql = self._insert % (self.table, self.column1, n, i)
            self.bc.do_sql(sql, (self.id, self.director_id) + values)
        except Exception as e:
            self.bc.do_sql(self._update % (self.table, m, self.column1), values + (self.id, self.director_id))
        return

        # }}}

class StoragePasswordStore(PasswordStore):
    '''The Storage daemons have slightly different requirements from Clients.
    Instantiate with a Storage ID and a Director ID.'''
    column1 = 'storage_id'
    table = 'storage_pwords'
    def __str__(self):
        d = bacula_tools.Director().search(self.director_id)
        return '%s: %s' % (d[NAME], self.password)
        
class DbDict(dict):
    '''Base class for all of the things derived from database rows.  It's badly
    overloaded with functionality, but it sure is convenient to do it this way.'''
    brace_re = re.compile(r'\s*(.*?)\s*\{\s*(.*)\s*\}\s*', re.MULTILINE|re.DOTALL)
    name_re = re.compile(r'^\s*name\s*=\s*(.*)', re.MULTILINE|re.IGNORECASE)
    bc = bacula_tools.Bacula_Factory()
    output = []
    SETUP_KEYS = []
    INT_KEYS = []
    BOOL_KEYS = []
    prefix = '  '               # Used for spacing out members when printing
    table = 'override me'       # This needs to be overridden in every subclass, before calling __init__
    IDTAG = 0                   # Only used for director/client/storage objects
    # {{{ __init__(row={}, string=None, **kwargs): pass in a row (as a dict)
    def __init__(self, row={}, string = None, **kwargs):
        '''Sets up instance variables and initializes the key/value pairs.
        If a row is passed in, update they keystore with it.
        If a string is passed in, it will be parsed via pyparsing.
        kwargs is *also* used for updating key/value pairs.'''
        dict.__init__(self)
        self.parser = None
        self.special = None
        self[ID] = None         # Ensure we have an ID
        self[NAME] = None       # Ensure we have an NAME
        # This allows flexibility in key setup/declaration, which in turn
        # will allow intelligent groupings to make parse/set/get code
        # somewhat simpler (or at least more clear).
        for x in dir(self):
            if not '_KEYS' in x: continue # Look only for, e.g., NULL_KEYS, SETUP_KEYS, TRUE_KEYS, etc
            for key in getattr(self, x):  # If it's a simple value,
                if type(key) == str: self[key] = None # Assign none
                else: self[key[0]] = key[1]           # Otherwise assume [1] is the desired default  value
        self.update(row)
        if string: self.parse_string(string)
        for key in kwargs: setattr(self, key, kwargs[key])
        self.word = self.table
        if self.word[-1] == 's': self.word = self.word[:-1]
        return

    # }}}
    # {{{ search(key=None):

    def search(self, key=None):
        '''Search for ourself using a number of different methods.  If no key is
        passed in, try self[NAME] and then self[ID].  Otherwise, try the
        passed-in key as an ID if it can be converted to an INT, otherwise
        assume it's a name.  In the event there is no proper row found,
        return a suggestion as to something better to search for, if
        possible.'''
        if not key:
            debug_print('DbDict.search: no key, checking for NAME and ID: table "%s", name "%s", id "%s"'% (self.table, self[NAME], self[ID]))
            if self[NAME]: new_me = self.bc.value_check(self.table, NAME, self[NAME], asdict=True)
            elif self[ID]: new_me = self.bc.value_check(self.table, ID, self[ID], asdict=True)
        else:
            if type(key) == list or type(key) == tuple: key=key[0]
            try: new_me = self.bc.value_check(self.table, ID, int(key), asdict=True)
            except: new_me = self.bc.value_check(self.table, NAME, key, asdict=True)
        try: self.update(new_me[0])
        except Exception as e: pass
        if self[ID]: [getattr(self, x)() for x in dir(self) if '_load_' in x]
        return self

    # }}}
    # {{{ delete(): delete it from the database

    def delete(self):
        '''Delete itself from the database.'''
        self.bc.do_sql('DELETE FROM %s WHERE id = %%s' % self.table, self[ID])
        return

# }}}
    # {{{ _set(field, value, boolean=False, dereference=False): handy shortcut for setting and saving values

    def _set(self, field, value, boolean=False, dereference=False):
        '''Instead of overriding the standard setter, I chose to add a separate
        function that will set and save.  We also do some special processing of
        boolean values.'''
        debug_print('setting %s to %s, boolean=%s, dereference=%s', field, value, boolean, dereference)
        if boolean and value != None:
            if value in TRUE_VALUES: value = 1
            elif value in FALSE_VALUES: value = 0
            else:
                print('"%s" is not a proper boolean value: %s not changed' % (value, field))
                return
        if dereference: value = self._fk_reference(field, value)[ID]
        if field == PASSWORD and value == GENERATE: value = bacula_tools.generate_password()
        self[field] = value
        return self._save()

    # }}}
    # {{{ _save(): Save the top-level fileset record

    def _save(self):
        '''Update the database with our data.'''
        if self[ID]:
            keys = [x for x in self.keys() if not x == ID]
            keys.sort()
            sql = 'UPDATE %s SET %s WHERE id = %%s' % (self.table,
                                                       ', '.join(['`%s` = %%s' % x for x in keys]))
            values = tuple([self[x] for x in keys] + [self[ID],])
            return self.bc.do_sql(sql, values)
        sql = 'INSERT INTO %s (`%s`) VALUES (%s)' % (self.table, '`,`'.join(self.keys()), ','.join(['%s' for x in self.keys()]))
        debug_print(sql, self.values())
        try:
            self.bc.do_sql(sql, tuple(self.values()))
            return self.search()
        except Exception as e:
            if e.args[0] == 1062: die('\t%s "%s" already exists.  You must delete it first.' % (self.word.capitalize(), self[NAME]))
            print(e)
            raise

# }}}
    # {{{ _set_name(name): set my name

    def _set_name(self, name):
        '''Search the database for an existing element associated with name and
        load it up.  Also, run any _load_ hooks that exist.

        '''
        row = self.bc.value_ensure(self.table, NAME, name.strip(), asdict=True)[0]
        self.update(row)
        [getattr(self, x)() for x in dir(self) if '_load_' in x]
        return

    # }}}
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        We're cheating and treating this object as a blob.  Also, the
        *_config parameters will potentially be used to tell us to discard
        passwords.  Sigh.
        '''
        g = self.name_re.search(string).groups()
        self._set_name(g[0].strip())
        string = self.name_re.sub('', string)
        data = '\n  '.join([x.strip() for x in string.split('\n') if x])
        self._set(DATA, data)
        return "%s: %s" % (self.table.capitalize(), self[NAME])

    # }}}
    # {{{ _parse_setter(key, c_int=False, dereference=False):

    def _parse_setter(self, key, c_int=False, dereference=False):
        '''Shortcut called by parser for setting values'''
        def rv(value):
            if c_int: self._set(key, int(value[2].strip()), dereference=dereference)
            else: self._set(key, value[2].strip(), dereference=dereference)
        return rv

# }}}
    # {{{ _simple_phrase(key, quoted=True):

    def _simple_phrase(self, key, quoted=True):
        '''Shortcut for formatting a simple key/value pair.'''
        if not type(key) == str: key = key[0]
        if self[key] == None: return
        if 'retention' in key: quoted = False
        if 'size' in key: quoted = False
        if 'bytes' in key: quoted = False
        try:
            int(self[key])
            value = self[key]
        except:
            if quoted: value = '"' + self[key] + '"'
            else: value = self[key]
        self.output.insert(-1,'%s%s = %s' % (self.prefix, key.capitalize(), value))
        return

    # }}}
    # {{{ _yesno_phrase(key):

    def _yesno_phrase(self, key):
        '''Formatting shortcut for string representation of booleans.'''
        if not type(key) == str: key = key[0]
        value = self[key]
        if value == None: return
        if value == '0': value = NO
        else: value = YES
        self.output.insert(-1,'%s%s = %s' % (self.prefix,key.capitalize(), value))
        return

    # }}}
    # {{{ fd(): stub function to make testing a little easier

    def fd(self):
        '''Stub'''
        return ''

    # }}}
    # {{{ _fk_reference(fk, string=None): Set/get fk-references

    def _fk_reference(self, fk, string=None):
        '''Shortcut for vivifying objects related to foreign keys'''
        debug_print('_fk_reference %s: %s, %s' % (fk, string, self[fk]))
        obj = bacula_tools._DISPATCHER[fk.replace('_id','')]()
        if string:
            obj.search(string.strip())
            if not obj[ID]: obj._set_name(string.strip())
            if not self[fk] == obj[ID]: self._set(fk, obj[ID])
        else: obj.search(self[fk])
        return obj

# }}}

    # Perhaps i'm overloading this class too much here, but
    # a) I can never remember how to do mix-ins, and
    # b) the things I want to do all reference internals.
    # {{{ cli(): Instantiate an option parser and add all the standard bits to it

    def cli(self):
        '''Builds and runs a CLI that applies to every DbDict-derived object.'''
        self.parser = optparse.OptionParser(description='Manage Bacula %ss.' % self.word,
                                            usage='usage: %%prog [options] [%s]' % self.word)
        self.parser.add_option('--create', action='store_true',
                               default=False, help='Create the given %s' % self.word)
        self.parser.add_option('--delete', action='store_true',
                               default=False, help='Delete the given %s' % self.word)
        self.parser.add_option('--rename', metavar='NEW_NAME',
                               help='Rename the given %s' % self.word)
        self.parser.add_option('--list', action='store_true',
                               default=False, help='List the available %ss' % self.word)
        self.parser.add_option('--clone', metavar='CLONE_NAME',
                               help='Duplicate the given %s' % self.word)

        # Add in various groups of things to set
        self._cli_parser_group(self.BOOL_KEYS, "Boolean Setters",
                               "Set with 0/1/yes/no/true/false or '' (empty string) to unset.",
                               metavar = '[yes|no]'
        )

        self._cli_parser_group(self.INT_KEYS, "Integer Setters",
                               "These accept integers or '' (empty string) to unset.", type='int', metavar='number')
        
        self._cli_parser_group(self.SETUP_KEYS, "Setters",
                               "These options are used for setting various values.  "
                               "Use an empty string, e.g. '' to unset the value for strings variables.  "
                               "You should be aware that no sanity checking is done here, so it is quite possible "
                               "to break your configuration while using them.  Caveat emptor."
                           )
        self._cli_special_setup()
        return self._cli_do_parse()

        # }}}
    # {{{ _cli_do_parse(): actually parse the CLI and act on it

    def _cli_do_parse(self):
        '''Parse the standard CLI options.'''
        (args, client_arg) = self.parser.parse_args()


        if args.delete and (args.create or args.rename or args.clone):
            die('','If you delete then there is no sense in doing anything else.',
                "You didn't think this one out very well, did you?.")

        if args.list:
            for row in self.bc.do_sql('select name from %s order by name' % self.table): print(row[0])
            if not client_arg: exit()

        if not client_arg:
            self.parser.print_help()
            exit()

        name_or_num = client_arg[0]
        if args.create: self._set_name(name_or_num)

        self.search(name_or_num)
        
        if not self[ID]:
            print('No such %s: %s' % (self.word, name_or_num))
            exit()

        if args.delete:
            self.delete()
            print('Deleted %s' % name_or_num)
            exit()                      # Nothing to print out now

        if args.rename: self._set(NAME, args.rename)

        if args.clone:
            oid = self[ID]
            self[ID] = None
            self[NAME] = args.clone
            self._save()
            self._cli_special_clone(oid)

        self._cli_option_processor(args, self.BOOL_KEYS, boolean=True)
        self._cli_option_processor(args, self.INT_KEYS)
        self._cli_option_processor(args, self.SETUP_KEYS)
        self._cli_special_do_parse(args)

        self._cli_printer()
        return

        # }}}
    # {{{ _cli_printer():

    def _cli_printer(self):
        '''Print the object out on the CLI'''
        maxlen = 10
        keylist = []
        for key in self.BOOL_KEYS + self.INT_KEYS + self.SETUP_KEYS:
            if not type(key) == str: key = key[0]
            keylist.append(key)
        keylist.sort()
        for key in keylist:
            if len(key) > maxlen: maxlen = len(key)
        maxlen += 4
        self._maxlen = maxlen
        fmt = '%' + str(maxlen) + 's: %s'
        print(fmt % ('ID', str(self[ID])))
        try: print(fmt % ('NAME', str(self[NAME])))
        except: pass            # One child class doesn't have a NAME
        for key in keylist: print(fmt % (key, str(self[key])))
        self._cli_special_print()
        return

    # }}}
    # {{{ _cli_parser_group(keys, label, help_message, **kwargs): add an option group to the CLI parser

    def _cli_parser_group(self, keys, label, help_message, **kwargs):
        '''Shortcut for creating a group of options.'''
        if not keys: return
        group = optparse.OptionGroup(self.parser, label, help_message)
        for key in keys:
            if not type(key) == str:
                if len(key) > 2: group.add_option('--' + key[0], help=key[2], **kwargs)
                else: group.add_option('--' + key[0], **kwargs)
            else: group.add_option('--' + key, **kwargs)
        self.parser.add_option_group(group)

        # }}}
    # {{{ _cli_option_processor(args, items, boolean=False, dereference=False):

    def _cli_option_processor(self, args, items, boolean=False, dereference=False):
        '''Shortcut to handle CLI options in a standard and easy way.'''
        for key in items:
            if not type(key) == str: key = key[0]
            value = getattr(args, key)
            if value == None: continue
            if value == '': value = None
            try: self._set(key, value, boolean, dereference)
            except: pass
        return

        # }}}
        
    # these empty functions provide placeholders for subclasses to call to
    # enable more complicated behaviors.
    def _cli_special_setup(self): pass
    def _cli_special_do_parse(self, args): pass
    def _cli_special_clone(self, oid): pass
    def _cli_special_print(self): pass

class PList(list):
    '''This bizarre construct takes a phrase and lazily turns it into a list
    that is all the permutations of the phrase with all spaces removed.
    Further, this list is sorted such that the first element is the
    original phrase, while the last one has no spaces at all.  It's kind of
    a weird thing, but it makes the string parsing declarations much, much
    more compact and efficient.

    '''
    # {{{ __init__(phrase):

    def __init__(self, phrase):
        list.__init__(self)
        result = self._p2(phrase.split(' '))
        result.sort()
        self.extend(result)
        return

    # }}}
    # {{{ _p2(ary):

    def _p2(self, ary):
        '''Recursive permutation function that returns either single string or a
        pair of strings, one of which is null-joined and the other of which is
        space-joined.'''
        if len(ary) == 1: return ary
        if len(ary) == 2: return [''.join(ary), ' '.join(ary)]
        results = []
        for x in self._p2(ary[1:]):
            results.append(ary[0] + x)
            results.append(ary[0] + ' ' + x)
        return results

    # }}}
    

class BSock:
    '''Sometimes, you want to talk to various Bacula daemons without the
    overhead of firing up bconsole, particularly since that will involve
    shell interaction as well fun parsing foo.  This will make it a bit
    easier, not to mention making dealing with timeouts a lot more
    mangeable.
    '''
# {{{ __init__(address, password, myname, port, debug=False, timeout=5):
    def __init__(self, address, password, myname, port, debug=False, timeout=5):
        '''Address, password, myname, and port are all mandatory.

        address = the destination with which you want to communicate. (None -> 127.0.0.1)
        myname = the "name" with which a password is associated.  This is not as obvious as you might hope.

        '''
        if not address: address = '127.0.0.1'
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(timeout) # Don't take forever trying to do stuff
        self.log('connecting to: %s' % str((address,port)))
        self.connection.connect((address,port))
        self.password = password
        self.name = myname
        self.DEBUG = debug
        return
# }}}
# {{{ log(msg): Debugging output

    def log(self, msg):
        '''Write out a single message to stderr, IFF self.DEBUG.'''
        if self.DEBUG:
            sys.stderr.write(msg)
            sys.stderr.flush()
        return

    # }}}
# {{{ auth(): authenticate a new connection

    def auth(self):
        '''Authenticated this client with the target service.

        I should note that, as written, the target service is *not* mutually authenticated.  

        The bulk of this was written by Matthew Ife, so thanks!'''
        
        self.send("Hello %s calling\n" % (self.name,)) # this is effectively our username
        challenge = self.recv() # Receive the challenge response
        m = re.search("auth cram-md5 (<.+?>)", challenge) # parse the challenge out of the returned string
        chal = m.group(1)
        
        pw = hashlib.md5(self.password).hexdigest()
        self.send(base64.b64encode(hmac.new(pw, chal).digest())[:-2]) # hmac and base64 encode the request

        result = self.recv() # receive response
        if result != "1000 OK auth\n": raise ValueError("Authentication Failed %s" % (result,))# failed

        # send our challenge response
        self.send("auth cram-md5 <%d.%d@%s> ssl=0\n" % (randint(1,99999999), int(time.time()), self.name))
        self.recv()                 # get the response back
        self.send("1000 OK auth\n") # Dont even check the response here!

        # This is basically cheating the protocol spec! :-)
        data = self.recv()
        if not re.match(".* OK.*",data): # auth complete
            raise ValueError("Unexpected packet received %s" % (data,))
        self.auth = True
        return data

    # }}}
# {{{ send(message): send a message to the remote daemon

    def send(self, message):
        '''Send a properly encoded messages to the connected service.'''
        ldata = pack('!i',len(message))
        self.connection.send(ldata)
        self.log( 'sending:  (%d) %s\n' % (len(message), message))
        self.connection.send(message)
        return

    # }}}
# {{{ recv(): Get a one line response from the remote daemon

    def recv(self):
        '''Read a (theoretically) single-line response from the connected service.'''
        msglen = unpack('!i', self.connection.recv(4))[0]
        if msglen < 0: return ''
        response = self.connection.recv(msglen)
        self.log( 'received: %s' % response)
        return response

    # }}}
# {{{ recv_all(): receive a multi-line response from the remote daemon

    def recv_all(self):
        """Gets all lines of a request"""
        r = ""
        s = self.recv()
        while s:
            r += s
            s = self.recv()
        return r

    # }}}
# {{{ version(): request version info from the remote daemon (useless?)

    def version(self):
        '''Request the version string from the connected services.'''
        self.send('version')
        return self.recv()

    # }}}
# {{{ status(args=''): request status of the remote daemon

    def status(self, args=''):
        '''Ask the connected service for its status.'''
        if args: self.send('.status %s' % args)
        else: self.send('status')
        return self.recv_all()

    # }}}
# {{{ _time(): format the time for uniqueifying various things

    def _time(self):
        '''Format the time for uniqueifying various things'''
        return time.strftime('%F_%H.%M.%S_00')

    # }}}
