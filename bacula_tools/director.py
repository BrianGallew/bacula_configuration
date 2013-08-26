from . import *
keylist = []

class Director(DbDict):
    NULL_KEYS = [ADDRESS, DIRADDRESSES,MONITOR,
                 FD_CONNECT_TIMEOUT, HEARTBEATINTERVAL, MAXIMUMCONSOLECONNECTIONS,
                 MAXIMUMCONCURRENTJOBS, PASSWORD, PIDDIRECTORY, QUERYFILE,
                 SCRIPTS_DIRECTORY, SD_CONNECT_TIMEOUT, SOURCEADDRESS, STATISTICS_RETENTION,
                 VERID, WORKINGDIRECTORY, MESSAGE_ID]
    SETUP_KEYS = [(PORT, 9101),(NAME, ''),]
    table = DIRECTORS
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
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

        def _handle_ip(*x):
            a,b,c =  x[2]
            return '  %s = { %s }' % (a,c[0])

        def _handle_diraddr(*x):
            a,b,c =  x[2]
            self._set(DIRADDRESSES, '  %s' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p
            
        gr_name = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_address = np((ADDRESS,), action=self._parse_setter(ADDRESS))
        gr_fd_conn = np(('fd connect timeout','fdconnect timeout','fd connecttimeout','fdconnecttimeout'), gr_number, self._parse_setter(FD_CONNECT_TIMEOUT, True))
        gr_heart = np(('heartbeat interval', 'heartbeatinterval',), gr_number, self._parse_setter(HEARTBEATINTERVAL, True))
        gr_max_con = np(('maximumconsoleconnections', 'maximumconsole connections', 'maximum consoleconnections', 'maximum console connections'),
                        gr_number, self._parse_setter(MAXIMUMCONSOLECONNECTIONS, True))
        gr_max_jobs = np(('maximum concurrent jobs', 'maximumconcurrent jobs', 'maximum concurrentjobs', 'maximumconcurrentjobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS, True))
        gr_pass = np((PASSWORD,), action=self._parse_setter(PASSWORD))
        gr_pid = np((PIDDIRECTORY, 'pid directory'), action=self._parse_setter(PIDDIRECTORY))
        gr_query = np(('query file', 'queryfile'), action=self._parse_setter(QUERYFILE))
        gr_scripts = np(('scripts directory', 'scriptsdirectory'), action=self._parse_setter(SCRIPTS_DIRECTORY))
        gr_sd_conn = np(('sd connect timeout', 'sdconnect timeout', 'sd connecttimeout', 'sdconnecttimeout'), gr_number, self._parse_setter(SD_CONNECT_TIMEOUT, True))
        gr_source = np(('source address', 'sourceaddress'), action=self._parse_setter(SOURCEADDRESS))
        gr_stats = np(('statistics retention', 'statisticsretention'), action=self._parse_setter(STATISTICS_RETENTION))
        gr_verid = np((VERID,), action=self._parse_setter(VERID))
        gr_messages = np((MESSAGES,), action=lambda x:self._parse_setter(MESSAGE_ID, dereference=True))
        gr_work_dir = np((WORKINGDIRECTORY, 'working directory'), action=self._parse_setter(WORKINGDIRECTORY))
        gr_port = np(('dirport', 'dir port'), gr_number, self._parse_setter(PORT, True))
        gr_monitor = np((MONITOR,), gr_yn, action=self._parse_setter(MONITOR))

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(('dir addresses', 'diraddresses'), nestedExpr('{','}', OneOrMore(da_ip)), _handle_diraddr)

        gr_res = OneOrMore(gr_name | gr_address | gr_fd_conn | gr_heart | gr_max_con | gr_max_jobs | gr_pass | gr_pid | gr_query | gr_scripts | gr_sd_conn | gr_source | gr_stats | gr_verid | gr_messages | gr_work_dir | gr_port | gr_monitor | da_addresses)

        result = gr_res.parseString(string, parseAll=True)
        return 'Director: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Director {\n  Name = "%(name)s"' % self,'}']
        self._simple_phrase(PORT)
        self.output.insert(-1, '  %s = "%s"' % (MESSAGES.capitalize(), self._fk_reference(MESSAGE_ID)[NAME]))
        if self[DIRADDRESSES]:
            self.output.insert(-1, '  %s {' % DIRADDRESSES.capitalize())
            self.output.insert(-1,  self[DIRADDRESSES])
            self.output.insert(-1, '  }')
        for key in self.NULL_KEYS:
            if key in [MESSAGE_ID, ID, DIRADDRESSES, MONITOR]: continue
            self._simple_phrase(key)
        return '\n'.join(self.output)

# }}}
    # {{{ fd(): return the string that describes the filedaemon configuration

    def fd(self):
        '''This is what we'll call to dump out the config for the file daemon'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        
        self._simple_phrase(PASSWORD)
        self._yesno_phrase(MONITOR)
        return '\n'.join(self.output)

    # }}}
        
  
