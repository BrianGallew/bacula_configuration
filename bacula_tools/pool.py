#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Pool(DbDict):
    BOOL_KEYS = [AUTOPRUNE, CATALOGFILES, RECYCLE, USEVOLUMEONCE,
                 RECYCLEOLDESTVOLUME, RECYCLECURRENTVOLUME, PURGEOLDESTVOLUME]
    SETUP_KEYS = [MAXIMUMVOLUMES, STORAGE, MAXIMUMVOLUMEJOBS, MAXIMUMVOLUMEFILES,
                  MAXIMUMVOLUMEBYTES, VOLUMEUSEDURATION, VOLUMERETENTION,
                  ACTIONONPURGE, SCRATCHPOOL, RECYCLEPOOL,
                  FILERETENTION, JOBRETENTION, CLEANINGPREFIX,
                  LABELFORMAT, (POOLTYPE, 'Backup', "Enum: ['Backup', 'Archive', 'Cloned', 'Migration', 'Copy', 'Save']")]
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
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np(PList('pool type'), action=self._parse_setter(POOLTYPE))
        gr_line = gr_line | np(PList('maximum volumes'), action=self._parse_setter(MAXIMUMVOLUMES))
        gr_line = gr_line | np((STORAGE,), action=self._parse_setter(STORAGE))
        gr_line = gr_line | np(PList('use volume once'), gr_yn, action=self._parse_setter(USEVOLUMEONCE))
        gr_line = gr_line | np(PList('catalog files'), gr_yn, action=self._parse_setter(CATALOGFILES))
        gr_line = gr_line | np(PList('auto prune'), gr_yn, action=self._parse_setter(AUTOPRUNE))
        gr_line = gr_line | np((RECYCLE,), gr_yn, action=self._parse_setter(RECYCLE))
        gr_line = gr_line | np(PList('recycle oldest volume'), gr_yn, action=self._parse_setter(RECYCLEOLDESTVOLUME))
        gr_line = gr_line | np(PList('recycle current volume'), gr_yn, action=self._parse_setter(RECYCLECURRENTVOLUME))
        gr_line = gr_line | np(PList('purge oldest volume'), gr_yn, action=self._parse_setter(PURGEOLDESTVOLUME))
        gr_line = gr_line | np(PList('maximum volume jobs'), gr_number, action=self._parse_setter(MAXIMUMVOLUMEJOBS))
        gr_line = gr_line | np(PList('maximum volume files'), gr_number, action=self._parse_setter(MAXIMUMVOLUMEFILES))
        gr_line = gr_line | np(PList('maximum volume bytes'), action=self._parse_setter(MAXIMUMVOLUMEBYTES))
        gr_line = gr_line | np(PList('volume use duration'), action=self._parse_setter(VOLUMEUSEDURATION))
        gr_line = gr_line | np(PList('volume retention'), action=self._parse_setter(VOLUMERETENTION))
        gr_line = gr_line | np(PList('action on purge'), action=self._parse_setter(ACTIONONPURGE))
        gr_line = gr_line | np(PList('scratch pool'), action=self._parse_setter(SCRATCHPOOL))
        gr_line = gr_line | np(PList('recycle pool'), action=self._parse_setter(RECYCLEPOOL))
        gr_line = gr_line | np(PList('file retention'), action=self._parse_setter(FILERETENTION))
        gr_line = gr_line | np(PList('job retention'), action=self._parse_setter(JOBRETENTION))
        gr_line = gr_line | np(PList('cleaning prefix'), action=self._parse_setter(CLEANINGPREFIX))
        gr_line = gr_line | np(PList('label format'), action=self._parse_setter(LABELFORMAT))

        gr_res = OneOrMore(gr_line)
        result = gr_res.parseString(string, parseAll=True)
        return 'Pool: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''String representation of a Pool formatted for inclusion in a config file.'''
        self.output = ['Pool {\n  Name = "%(name)s"' % self,'}']
        for key in self.SETUP_KEYS: self._simple_phrase(key)
        for key in self.BOOL_KEYS: self._yesno_phrase(key)

        return '\n'.join(self.output)

# }}}

def main():
    s = Pool()
    s.cli()

if __name__ == "__main__": main()
