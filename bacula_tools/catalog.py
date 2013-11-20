#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Catalog(DbDict):
    SETUP_KEYS = [DBADDRESS, DBNAME, DBPORT, DBSOCKET, PASSWORD, USER]
    SPECIAL_KEYS = [DIRECTOR_ID,]
    table = CATALOGS
    # {{{ parse_string(string, director): Entry point for a recursive descent parser

    def parse_string(self, string, director):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith, nums, printables
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np((USER, 'dbuser', 'db user'), action=self._parse_setter(USER))
        gr_line = gr_line | np((PASSWORD, 'dbpassword', 'db password'), action=self._parse_setter(PASSWORD))
        gr_line = gr_line | np(PList(DBSOCKET), action=self._parse_setter(DBSOCKET))
        gr_line = gr_line | np(PList(DBPORT), gr_number, action=self._parse_setter(DBPORT))
        gr_line = gr_line | np(PList('db name'), action=self._parse_setter(DBNAME))
        gr_line = gr_line | np(PList('db address'), action=self._parse_setter(DBADDRESS))
        gr_res = OneOrMore(gr_line)

        result = gr_res.parseString(string, parseAll=True)
        self._set(DIRECTOR_ID, director[ID])
        return 'Catalog: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''Convert a Catalog into its string representation.  The result can be
        inserted directly into the configuration of the director.'''
        self.output = ['Catalog {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        return '\n'.join(self.output)

# }}}
    # {{{ search(key=None):

    def search(self, key=None):
        '''Override the standard self.search() function to look up a catalog by
        Director ID.  This is primarily used when generating the
        configuration for a director, as you'll have a Director ID and need
        to look up the associated catalog.'''
        DbDict.search(self, key)
        if self[ID]: return self
        if not self[DIRECTOR_ID]: return self # can't look myself up if I don't have any attributes
        new_me = self.bc.value_check(self.table, DIRECTOR_ID, self[DIRECTOR_ID], asdict=True)
        try: self.update(new_me[0])
        except Exception as e: pass
        [getattr(self, x)() for x in dir(self) if '_load_' in x]
        return self

    # }}}
    # {{{ _cli_special_setup(): add in Director ID support

    def _cli_special_setup(self):
        self.parser.add_option('--director', help='The name or ID of the Director that uses this catalog')
        return

    # }}}
    # {{{ _cli_special_do_parse(args): handle Director ID parsing

    def _cli_special_do_parse(self, args):
        '''It should be noted that a Catalog can be associated with one, and only
        one, Director.  This function handles changing the Director from the CLI.'''
        if args.director == None: return # Nothing to do!
        d = bacula_tools.Director()
        d.search(args.director)
        if not d[ID]: d.search(args.director)
        if not d[ID]:
            print('\n***WARNING***: Unable to find a director using "%s".  Association not changed\n' % args.director)
            return
        self._set(DIRECTOR_ID, d[ID])
        return

# }}}
    # {{{ _cli_special_print(): print out passwords

    def _cli_special_print(self):
        '''De-reference the Director and print its name.'''
        d = bacula_tools.Director().search(self[DIRECTOR_ID])
        fmt = '%' + str(self._maxlen) +'s: %s'
        print(fmt % (DIRECTOR, d[NAME]))
        return

    # }}}

# Implement the CLI for managing Catalogs
def main():
    s = Catalog()
    s.cli()

if __name__ == "__main__": main()
