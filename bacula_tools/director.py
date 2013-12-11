#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Director(DbDict):
    SETUP_KEYS = [ADDRESS, 
                 FD_CONNECT_TIMEOUT, HEARTBEATINTERVAL,
                 PASSWORD, PIDDIRECTORY, QUERYFILE,
                 SCRIPTS_DIRECTORY, SD_CONNECT_TIMEOUT, SOURCEADDRESS, STATISTICS_RETENTION,
                 WORKINGDIRECTORY, DIRADDRESSES]
    INT_KEYS = [(DIRPORT, 9101), MAXIMUMCONCURRENTJOBS, MAXIMUMCONSOLECONNECTIONS,]
    NULL_KEYS = [MESSAGES_ID, ]
    table = DIRECTORS
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 1
    # {{{ parse_string(string, director_config, obj): Entry point for a recursive descent parser

    def parse_string(self, string, director_config, obj):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        FTR: this is hideous.
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith, nums, printables
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def _handle_password(*x):
            a,b,c =  x[2]
            if type(obj) == bacula_tools.Client: klass = PasswordStore
            elif type(obj) == bacula_tools.Storage: klass = StoragePasswordStore
            else: print("WTH is a", type(obj), "being passed in?", director_config)
            a = klass(obj[ID], self[ID])
            a.password = c
            a.store()
            return

        def _handle_monitor(*x):
            a,b,c =  x[2]
            a = PasswordStore(obj[ID], self[ID])
            a.monitor = c
            a.store()
            return

        def _handle_ip(*x):
            a,b,c =  x[2]
            return '  %s = { %s }' % (a,c[0])

        def _handle_diraddr(*x):
            a,b,c =  x[2]
            self._set(DIRADDRESSES, '  %s' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p
            
        gr_name = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_address = np((ADDRESS,), action=self._parse_setter(ADDRESS))
        gr_fd_conn = np(PList('fd connect timeout'), gr_number, self._parse_setter(FD_CONNECT_TIMEOUT, True))
        gr_heart = np(PList('heartbeat interval'), gr_number, self._parse_setter(HEARTBEATINTERVAL, True))
        gr_max_con = np(PList('maximum console connections'),
                        gr_number, self._parse_setter(MAXIMUMCONSOLECONNECTIONS, True))
        gr_max_jobs = np(PList('maximum concurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS, True))
        gr_pid = np(PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
        gr_query = np(PList('query file'), action=self._parse_setter(QUERYFILE))
        gr_scripts = np(PList('scripts directory'), action=self._parse_setter(SCRIPTS_DIRECTORY))
        gr_sd_conn = np(PList('sd connect timeout'), gr_number, self._parse_setter(SD_CONNECT_TIMEOUT, True))
        gr_source = np(PList('source address'), action=self._parse_setter(SOURCEADDRESS))
        gr_stats = np(PList('statistics retention'), action=self._parse_setter(STATISTICS_RETENTION))
        gr_messages = np((MESSAGES,), action=self._parse_setter(MESSAGES_ID, dereference=True))
        gr_work_dir = np(PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
        gr_port = np(PList('dir port'), gr_number, self._parse_setter(DIRPORT, True))
        gr_monitor = np((MONITOR,), gr_yn, action=_handle_monitor)

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(PList('dir addresses'), nestedExpr('{','}', OneOrMore(da_ip)), _handle_diraddr)

        # if this isn't a director, then we ignore the password
        if director_config: gr_pass = np((PASSWORD,), action=self._parse_setter(PASSWORD))
        else: gr_pass = np((PASSWORD,), action=_handle_password)

        gr_res = OneOrMore(gr_name | gr_address | gr_fd_conn | gr_heart | gr_max_con | gr_max_jobs | gr_pass | gr_pid | gr_query | gr_scripts | gr_sd_conn | gr_source | gr_stats | gr_messages | gr_work_dir | gr_port | gr_monitor | da_addresses)

        result = gr_res.parseString(string, parseAll=True)
        return 'Director: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''String representation of a Director, suitable for inclusion in director.conf'''
        self.output = ['Director {\n  Name = "%(name)s"' % self,'}']
        for key in self.NULL_KEYS: self._simple_phrase(key)
        # set the messages
        m = self._fk_reference(MESSAGES_ID)
        self.output.insert(-1, '  %s = "%s"' % (MESSAGES.capitalize(), m[NAME]))
        if self[DIRADDRESSES]:
            self.output.insert(-1, '  %s {' % DIRADDRESSES.capitalize())
            self.output.insert(-1,  self[DIRADDRESSES])
            self.output.insert(-1, '  }')
        return '\n'.join(self.output)

# }}}
    # {{{ fd(): return the string that describes the filedaemon configuration

    def fd(self):
        '''This is what we'll call to dump out the config for the file daemon'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        if getattr(self,CLIENT_ID, None):
            a = PasswordStore(self.client_id, self[ID])
            if getattr(a,PASSWORD, None):
                self.output.insert(-1,'  Password = "%s"' % a.password)
                if a.monitor: self.output.insert(-1,'  Monitor = "yes"' )
        return '\n'.join(self.output)

    # }}}
    # {{{ sd(): return the string that describes the storagedaemon configuration

    def sd(self):
        '''This is what we'll call to dump out the config for the storage daemon'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        if getattr(self,STORAGE_ID, None):
            a = StoragePasswordStore(self.storage_id, self[ID])
            if getattr(a,PASSWORD, None):
                self.output.insert(-1,'  Password = "%s"' % a.password)
        return '\n'.join(self.output)

    # }}}
    # {{{ bconsole(): return the string that describes the storagedaemon configuration

    def bconsole(self):
        '''This is what we'll call to dump out the config for the bconsole'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        self._simple_phrase(DIRPORT)
        self._simple_phrase(ADDRESS)
        self._simple_phrase(PASSWORD)
        return '\n'.join(self.output)

    # }}}
    # {{{ _cli_special_setup(): setup the weird phrases that go with directors

    def _cli_special_setup(self):
        '''Handle setting by the CLI of the Message to be used by this %s.''' % self.word.capitalize()
        group = optparse.OptionGroup(self.parser,
                                     "Object Setters",
                                     "Various objects associated with a %s" % self.word.capitalize())
        group.add_option('--message-set')
        self.parser.add_option_group(group)
        return

    # }}}
    # {{{ _cli_special_do_parse(args): handle the weird phrases that go with directors

    def _cli_special_do_parse(self, args):
        '''Enable the CLI to set the Message to be used by this Director.'''
        if args.message_set == None: return
        if args.message_set =='': return self._set(MESSAGES_ID, None)
        target = Messages().search(args.message_set)
        if target[ID]: self._set(MESSAGES_ID, target[ID])
        else: print('Unable to find a match for %s, continuing' % args.message_set)
        return

# }}}
    # {{{ _cli_special_print(): print out the weird phrases that go with directors

    def _cli_special_print(self):
        '''Print out the Message for this Director'''
        if not self[MESSAGES_ID]: return
        fmt = '%' + str(self._maxlen) + 's: %s'
        print(fmt % ('Messages', self._fk_reference(MESSAGES_ID)[NAME]))
        return
    # }}}

def main():
    s = Director()
    s.cli()

if __name__ == "__main__": main()
