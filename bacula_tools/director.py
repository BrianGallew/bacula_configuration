from . import *
from pprint import pprint
keylist = []

class Director(DbDict):
    NULL_KEYS = [ID, ADDRESS, DIRADDRESSES,
                 FD_CONNECT_TIMEOUT, HEARTBEAT_INTERVAL, MAXIMUMCONSOLECONNECTIONS,
                 MAXIMUM_CONCURRENT_JOBS, PASSWORD, PID_DIRECTORY, QUERYFILE,
                 SCRIPTS_DIRECTORY, SD_CONNECT_TIMEOUT, SOURCEADDRESS, STATISTICS_RETENTION,
                 VERID, WORKING_DIRECTORY, MESSAGE_ID]
    SETUP_KEYS = [(PORT, 9101),(NAME, ''),]
    table = DIRECTORS
    # {{{ _set_messages(string):

    def _set_messages(self, string):
        m = Messages()
        m.search(string.strip())
        self._set(MESSAGE_ID, m[ID])

        # }}}
    # {{{ _get_messages(string):

    def _get_messages(self):
        sql = 'select %s from %s where id = %%s' % (NAME,MESSAGES)
        row = self.bc.do_sql(sql, self[MESSAGE_ID])[0]
        return row[0]

        # }}}
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

        def _setter(key, c_int=False):
            def rv(value):
                if c_int: self._set(key, int(value[2]))
                else: self._set(key, value[2])
            return rv

        def _handle_ip(*x):
            a,b,c =  x[2]
            return '  %s = { %s }' % (a,c[0])

        def _handle_diraddr(*x):
            a,b,c =  x[2]
            self._set(DIRADDRESSES, '{\n  %s\n  }' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p
            
        gr_name = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_address = np((ADDRESS,), action=_setter(ADDRESS))
        gr_fd_conn = np(('fd connect timeout','fdconnect timeout','fd connecttimeout','fdconnecttimeout'), gr_number, _setter(FD_CONNECT_TIMEOUT, True))
        gr_heart = np(('heartbeat interval', 'heartbeatinterval',), gr_number, _setter(HEARTBEAT_INTERVAL, True))
        gr_max_con = np(('maximumconsoleconnections', 'maximumconsole connections', 'maximum consoleconnections', 'maximum console connections'),
                        gr_number, _setter(MAXIMUMCONSOLECONNECTIONS, True))
        gr_max_jobs = np(('maximum concurrent jobs', 'maximumconcurrent jobs', 'maximum concurrentjobs', 'maximumconcurrentjobs'), gr_number, action=_setter(MAXIMUM_CONCURRENT_JOBS, True))
        gr_pass = np((PASSWORD,), action=_setter(PASSWORD))
        gr_pid = np(('pid directory', 'piddirectory'), action=_setter(PID_DIRECTORY))
        gr_query = np(('query file', 'queryfile'), action=_setter(QUERYFILE))
        gr_scripts = np(('scripts directory', 'scriptsdirectory'), action=_setter(SCRIPTS_DIRECTORY))
        gr_sd_conn = np(('sd connect timeout', 'sdconnect timeout', 'sd connecttimeout', 'sdconnecttimeout'), gr_number, _setter(SD_CONNECT_TIMEOUT, True))
        gr_source = np(('source address', 'sourceaddress'), action=_setter(SOURCEADDRESS))
        gr_stats = np(('statistics retention', 'statisticsretention'), action=_setter(STATISTICS_RETENTION))
        gr_verid = np((VERID,), action=_setter(VERID))
        gr_messages = np((MESSAGES,), action=lambda x:self._set_messages(x[2]))
        gr_work_dir = np(('working directory', 'workingdirectory'), action=_setter(WORKING_DIRECTORY))
        gr_port = np(('dirport', 'dir port'), gr_number, _setter(PORT, True))

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(('dir addresses', 'diraddresses'), nestedExpr('{','}', OneOrMore(da_ip)), _handle_diraddr)

        gr_res = OneOrMore(gr_name | gr_address | gr_fd_conn | gr_heart | gr_max_con | gr_max_jobs | gr_pass | gr_pid | gr_query | gr_scripts | gr_sd_conn | gr_source | gr_stats | gr_verid | gr_messages | gr_work_dir | gr_port | da_addresses)

        result = gr_res.parseString(string, parseAll=True)
        print 'Director:', self[NAME]
        return

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        output = ['Director {\n  Name = %(name)s' % self,]
        output.append('  %s = %s' % (PORT.capitalize(), self[PORT]))
        output.append('  %s = %s' % (MESSAGES.capitalize(), self._get_messages()))
        
        for key in self.NULL_KEYS:
            if key in [MESSAGE_ID, ID]: continue
            if not self[key]: continue
            output.append('  %s = %s' % (key.capitalize(), self[key]))
        output.append('}')
        return '\n'.join(output)

# }}}
        
  
