#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *  #pragma: no cover

class Console(DbDict):
    '''This is for configuring bconsole access.  Unfortunately, there's no good
    way to extract this for constructing a bconsole.conf.  You can set up
    conventions that a client hostname should match the name of the Console,
    but that isn't going to be very satisfactory.

    TODO: this needs to be re-architected, along with the Director class.
    The Console shows up as a "Director" resource in the FD/SD, which is
    really quite stupid.

    '''
    SETUP_KEYS = [CATALOGACL, CLIENTACL, COMMANDACL, FILESETACL, JOBACL,
                  POOLACL, SCHEDULEACL, STORAGEACL, WHEREACL]
    table = CONSOLES
    IDTAG = 4
    def parse_string(self, string, director_config, obj):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import quotedString, restOfLine, Keyword, nestedExpr, OneOrMore, Word, Literal, removeQuotes, replaceWith
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        def _handle_monitor(*x): pass

        def _handle_password(*x):
            a,b,c =  x[2]
            p = PasswordStore(obj, self)
            p.password = c
            p.store()
            return

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        for key in self.SETUP_KEYS:
            if key == PASSWORD: continue
            gr_line = gr_line | np((key,), action=self._parse_setter(key))
        gr_monitor = np((MONITOR,), gr_yn, action=_handle_monitor)
        gr_pass = np((PASSWORD,), action=_handle_password)

        gr_res = OneOrMore(gr_line|gr_monitor|gr_pass)
        result = gr_res.parseString(string, parseAll=True)
        return 'Console: ' + self[NAME]

    def __str__(self):
        self.output = ['Console {\n  Name = "%(name)s"' % self, '}']
        
        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        return '\n'.join(self.output)

    def fd(self):
        self.output = ['Director {\n  Name = "%(name)s"' % self, '  Monitor = yes','}']
        self._simple_phrase(PASSWORD)
        return '\n'.join(self.output)



def main(): # Implement the CLI for managing Consoles
    s = Console()
    s.cli()

if __name__ == "__main__": main()
