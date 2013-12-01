#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Console(DbDict):
    '''This is for configuring bconsole access.  Unfortunately, there's no good
    way to extract this for constructing a bconsole.conf.  You can set up
    conventions that a client hostname should match the name of te Console,
    but that isn't going to be very satisfactory.

    '''
    SETUP_KEYS = [CATALOGACL, CLIENTACL, COMMANDACL, FILESETACL, JOBACL, PASSWORD,
                  POOLACL, SCHEDULEACL, STORAGEACL, WHEREACL]
    table = CONSOLES
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import quotedString, restOfLine, Keyword, nestedExpr, OneOrMore, Word, Literal, removeQuotes
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        for key in self.NULL_KEYS:
            if key == id: continue
            gr_line = gr_line | np((key,), action=self._parse_setter(key))

        gr_res = OneOrMore(gr_line)
        result = gr_res.parseString(string, parseAll=True)
        return 'Console: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Console {\n  Name = "%(name)s"' % self, '}']
        
        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        return '\n'.join(self.output)

# }}}


# Implement the CLI for managing Consoles
def main():
    s = Console()
    s.cli()

if __name__ == "__main__": main()
