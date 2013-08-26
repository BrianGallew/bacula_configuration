from . import *
keylist = []

class Pool(DbDict):
    NULL_KEYS = [
        MAXIMUMVOLUMES, STORAGE, USEVOLUMEONCE, MAXIMUMVOLUMEJOBS, MAXIMUMVOLUMEFILES,
        MAXIMUMVOLUMEBYTES, VOLUMEUSEDURATION, CATALOGFILES, AUTOPRUNE, VOLUMERETENTION,
        ACTIONONPURGE, SCRATCHPOOL, RECYCLEPOOL, RECYCLE, RECYCLEOLDESTVOLUME,
        RECYCLECURRENTVOLUME, PURGEOLDESTVOLUME, FILERETENTION, JOBRETENTION, CLEANINGPREFIX,
        LABELFORMAT
        ]
    SETUP_KEYS = [(NAME, ''), (POOLTYPE, 'Backup')]
    table = POOLS
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith, nums
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np((POOLTYPE, 'pool type'), action=self._parse_setter(POOLTYPE))
        gr_line = gr_line | np((MAXIMUMVOLUMES,'maximum volumes'), action=self._parse_setter(MAXIMUMVOLUMES))
        gr_line = gr_line | np((STORAGE,), action=self._parse_setter(STORAGE))
        gr_line = gr_line | np((USEVOLUMEONCE, 'use volume once', 'usevolume once', 'use volumeonce'), gr_yn, action=self._parse_setter(USEVOLUMEONCE))
        gr_line = gr_line | np((CATALOGFILES, 'catalog files'), gr_yn, action=self._parse_setter(CATALOGFILES))
        gr_line = gr_line | np((AUTOPRUNE, 'auto prune'), gr_yn, action=self._parse_setter(AUTOPRUNE))
        gr_line = gr_line | np((RECYCLE,), gr_yn, action=self._parse_setter(RECYCLE))
        gr_line = gr_line | np((RECYCLEOLDESTVOLUME, 'recycle oldest volume', 'recycle oldestvolume', 'recycleoldest volume'), gr_yn, action=self._parse_setter(RECYCLEOLDESTVOLUME))
        gr_line = gr_line | np((RECYCLECURRENTVOLUME, 'recycle current volume', 'recycle currentvolume', 'recyclecurrent volume'), gr_yn, action=self._parse_setter(RECYCLECURRENTVOLUME))
        gr_line = gr_line | np((PURGEOLDESTVOLUME, 'purge oldest volume', 'purge oldestvolume', 'purgeoldest volume'), gr_yn, action=self._parse_setter(PURGEOLDESTVOLUME))
        gr_line = gr_line | np((MAXIMUMVOLUMEJOBS, 'maximum volume jobs', 'maximum volumejobs', 'maximumvolume jobs'), gr_number, action=self._parse_setter(MAXIMUMVOLUMEJOBS))
        gr_line = gr_line | np((MAXIMUMVOLUMEFILES, 'maximum volume files', 'maximum volumefiles', 'maximumvolume files'), gr_number, action=self._parse_setter(MAXIMUMVOLUMEFILES))
        gr_line = gr_line | np((MAXIMUMVOLUMEBYTES, 'maximum volume bytes', 'maximum volumebytes', 'maximumvolume bytes'), action=self._parse_setter(MAXIMUMVOLUMEBYTES))
        gr_line = gr_line | np((VOLUMEUSEDURATION, 'volume use duration', 'volume useduration', 'volumeuse duration'), action=self._parse_setter(VOLUMEUSEDURATION))
        gr_line = gr_line | np((VOLUMERETENTION, 'volume retention'), action=self._parse_setter(VOLUMERETENTION))
        gr_line = gr_line | np((ACTIONONPURGE, 'action on purge', 'action onpurge', 'actionon purge'), action=self._parse_setter(ACTIONONPURGE))
        gr_line = gr_line | np((SCRATCHPOOL, 'scratch pool'), action=self._parse_setter(SCRATCHPOOL))
        gr_line = gr_line | np((RECYCLEPOOL, 'recycle pool'), action=self._parse_setter(RECYCLEPOOL))
        gr_line = gr_line | np((FILERETENTION, 'file retention'), action=self._parse_setter(FILERETENTION))
        gr_line = gr_line | np((JOBRETENTION, 'job retention'), action=self._parse_setter(JOBRETENTION))
        gr_line = gr_line | np((CLEANINGPREFIX, 'cleaning prefix'), action=self._parse_setter(CLEANINGPREFIX))
        gr_line = gr_line | np((LABELFORMAT, 'label format'), action=self._parse_setter(LABELFORMAT))

        gr_res = OneOrMore(gr_line)
        result = gr_res.parseString(string, parseAll=True)
        return 'Pool: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Pool {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.NULL_KEYS:
            if key in [ID, USEVOLUMEONCE, CATALOGFILES, AUTOPRUNE, RECYCLE, RECYCLEOLDESTVOLUME, RECYCLECURRENTVOLUME, PURGEOLDESTVOLUME]: continue
            self._simple_phrase(key)
        self._yesno_phrase(USEVOLUMEONCE, onlytrue=True)
        self._yesno_phrase(CATALOGFILES, onlyfalse=True)
        self._yesno_phrase(AUTOPRUNE, onlyfalse=True)
        self._yesno_phrase(RECYCLE, onlyfalse=True)
        self._yesno_phrase(RECYCLEOLDESTVOLUME, onlytrue=True)
        self._yesno_phrase(RECYCLECURRENTVOLUME, onlytrue=True)
        self._yesno_phrase(PURGEOLDESTVOLUME, onlytrue=True)
        return '\n'.join(self.output)

# }}}
