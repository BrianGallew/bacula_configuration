from . import *

class Storage(DbDict):
    NULL_KEYS = [
        SDPORT, ADDRESS, PASSWORD, DEVICE, MEDIATYPE, MAXIMUMCONCURRENTJOBS,
        HEARTBEATINTERVAL
        ]
    SD_KEYS = [WORKINGDIRECTORY, PIDDIRECTORY, CLIENTCONNECTWAIT, SDADDRESSES]
    BOOL_KEYS = [
        (AUTOCHANGER, 0), (ALLOWCOMPRESSION, 1)
        ]
    SETUP_KEYS = [(NAME, ''),]
    table = STORAGE
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
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

        def _handle_addr(*x):
            a,b,c =  x[2]
            self._set(SDADDRESSES, '  %s' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np(PList('sd port'), gr_number, action=self._parse_setter(SDPORT))
        gr_line = gr_line | np((ADDRESS,'sd address', SDADDRESS), action=self._parse_setter(ADDRESS))
        gr_line = gr_line | np((PASSWORD,), action=self._parse_setter(PASSWORD))
        gr_line = gr_line | np((DEVICE,), action=self._parse_setter(DEVICE))
        gr_line = gr_line | np(PList('media type'), action=self._parse_setter(MEDIATYPE))
        gr_line = gr_line | np(PList('auto changer'), gr_yn, action=self._parse_setter(AUTOCHANGER))
        gr_line = gr_line | np(PList('maximum concurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
        gr_line = gr_line | np(PList('allow compression'), gr_yn, action=self._parse_setter(ALLOWCOMPRESSION))
        gr_line = gr_line | np(PList('heartbeat interval'), action=self._parse_setter(HEARTBEATINTERVAL))

        gr_line = gr_line | np(PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
        gr_line = gr_line | np(PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
        gr_line = gr_line | np(PList('client connect wait'), action=self._parse_setter(CLIENTCONNECTWAIT))

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(PList('sd addresses'), nestedExpr('{','}', OneOrMore(da_ip)), _handle_addr)


        gr_res = OneOrMore(gr_line)
        result = gr_res.parseString(string, parseAll=True)
        return 'Storage: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Storage {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.NULL_KEYS:
            self._simple_phrase(key)
        self._yesno_phrase(AUTOCHANGER, onlytrue=True)
        self._yesno_phrase(ALLOWCOMPRESSION, onlyfalse=True)
        return '\n'.join(self.output)

# }}}
    # {{{ sd(): 

    def sd(self):
        self.output = ['Storage {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.SD_KEYS: self._simple_phrase(key)
        self._simple_phrase(SDPORT)
        self._simple_phrase(MAXIMUMCONCURRENTJOBS)
        self._simple_phrase(HEARTBEATINTERVAL)

        # Special keys
        if self[ADDRESS]: self.output.insert(-1,'%sSDAddress = %s' % (self.prefix, '"' + self[ADDRESS] + '"'))
        self._simple_phrase(SDADDRESSES)

        return '\n'.join(self.output)

# }}}
