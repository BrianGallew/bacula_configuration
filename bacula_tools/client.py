from . import *
keylist = []

class Client(DbDict):
    NULL_KEYS = [
        ADDRESS, CATALOG_ID, PASSWORD, FILERETENTION, JOBRETENTION, PRIORITY,
        WORKINGDIRECTORY, SDCONNECTTIMEOUT, MAXIMUMNETWORKBUFFERSIZE,
        PIDDIRECTORY, HEARTBEATINTERVAL, FDADDRESSES, FDADDRESS,
        FDSOURCEADDRESS, MAXIMUMBANDWIDTHPERJOB, PKIKEYPAIR, PKIMASTERKEY,
        NOTES,
        ]
    SETUP_KEYS = [(NAME, ''),(FDPORT, 9102), (AUTOPRUNE, 1), (MAXIMUMCONCURRENTJOBS, 1),
                  (PKIENCRYPTION, 0), (PKISIGNATURES, 0),]
    table = CLIENTS
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import quotedString, restOfLine, Keyword, nestedExpr, OneOrMore, Word, Literal, removeQuotes, nums, replaceWith, printables
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def _handle_ip(*x):
            a,b,c =  x[2]
            return '  %s = { %s }' % (a,c[0])

        def _handle_fdaddr(*x):
            a,b,c =  x[2]
            self._set(FDADDRESSES, '  %s' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np((ADDRESS,), action=self._parse_setter(ADDRESS))
        gr_line = gr_line | np((CATALOG,), action=self._parse_setter(CATALOG_ID, dereference=True))
        gr_line = gr_line | np((PASSWORD,), action=self._parse_setter(PASSWORD))
        gr_line = gr_line | np((FILERETENTION,'file retention'), action=self._parse_setter(FILERETENTION))
        gr_line = gr_line | np((JOBRETENTION,'job retention'), action=self._parse_setter(JOBRETENTION))
        gr_line = gr_line | np((PRIORITY,), gr_number, action=self._parse_setter(PRIORITY))
        gr_line = gr_line | np((WORKINGDIRECTORY,'working directory'), action=self._parse_setter(WORKINGDIRECTORY))
        gr_line = gr_line | np((PIDDIRECTORY,'pid directory'), action=self._parse_setter(PIDDIRECTORY))
        gr_line = gr_line | np((HEARTBEATINTERVAL, 'heartbeat interval', 'heart beat interval',),
                               action=self._parse_setter(HEARTBEATINTERVAL))
        gr_line = gr_line | np((FDADDRESS,'fd address'), action=self._parse_setter(FDADDRESS))
        gr_line = gr_line | np((FDSOURCEADDRESS, 'fd source address', 'fdsource address', 'fd sourceaddress',),
                               action=self._parse_setter(FDSOURCEADDRESS))
        gr_line = gr_line | np((PKIKEYPAIR, 'pki key pair','pkikey pair','pki keypair',),
                               action=self._parse_setter(PKIKEYPAIR))
        gr_line = gr_line | np((PKIMASTERKEY, 'pki master key', 'pkimaster key', 'pki masterkey',),
                               action=self._parse_setter(PKIMASTERKEY))
        gr_line = gr_line | np((FDPORT,'fd port'), gr_number, action=self._parse_setter(FDPORT))
        gr_line = gr_line | np((AUTOPRUNE,'auto prune'), gr_yn, action=self._parse_setter(AUTOPRUNE))
        gr_line = gr_line | np((MAXIMUMCONCURRENTJOBS, 'maximum concurrent jobs', 'maximumconcurrent jobs', 'maximum concurrentjobs',),
                               gr_number, action=self._parse_setter(FDPORT))
        gr_line = gr_line | np((PKIENCRYPTION, 'pki encryption',), gr_yn, action=self._parse_setter(PKIENCRYPTION))
        gr_line = gr_line | np((PKISIGNATURES, 'pki signatures',),
                               gr_yn, action=self._parse_setter(PKISIGNATURES))

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(('fd addresses', FDADDRESSES), nestedExpr('{','}', OneOrMore(da_ip)), _handle_fdaddr)

        gr_res = OneOrMore(gr_line|da_addresses)
        result = gr_res.parseString(string, parseAll=True)
        return 'Client: ' + self[NAME]


    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Client {\n  Name = "%(name)s"' % self,'}']
        self.output.insert(-1, '  %s = "%s"' % (CATALOG.capitalize(), self._fk_reference(CATALOG_ID)[NAME]))
        
        for key in [NAME, ADDRESS, FDPORT, PASSWORD, FILERETENTION,
                    JOBRETENTION, MAXIMUMCONCURRENTJOBS,
                    MAXIMUMBANDWIDTHPERJOB, PRIORITY
                    ]:
            self._simple_phrase(key)
        self._yesno_phrase(AUTOPRUNE)
        return '\n'.join(self.output)

# }}}
    # {{{ fd(): return the string that describes the filedaemon configuration

    def fd(self):
        '''This is what we'll call to dump out the config for the file daemon'''
        self.output = ['Client {\n  Name = "%(name)s"' % self, '}']
        
        for key in [WORKINGDIRECTORY, PIDDIRECTORY, HEARTBEATINTERVAL, MAXIMUMCONCURRENTJOBS,
                    FDPORT, FDADDRESS, FDSOURCEADDRESS, SDCONNECTTIMEOUT,
                    MAXIMUMNETWORKBUFFERSIZE, MAXIMUMBANDWIDTHPERJOB, PKIKEYPAIR, PKIMASTERKEY
                    ]:
            self._simple_phrase(key)
        if self[FDADDRESSES]:
            self.output.insert(-1, '  %s {' % FDADDRESSES.capitalize())
            self.output.insert(-1,  self[FDADDRESSES])
            self.output.insert(-1, '  }')
        self._yesno_phrase(PKIENCRYPTION, True)
        self._yesno_phrase(PKISIGNATURES, True)
        return '\n'.join(self.output)

    # }}}
