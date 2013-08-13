from . import *
from pprint import pprint
keylist = []

class Catalog(DbDict):
    NULL_KEYS = [
        ID, DBADDRESS, DBNAME, DBPORT, DBSOCKET, PASSWORD, USER, DIRECTOR_ID
        ]
    SETUP_KEYS = [(NAME, ''),]
    table = CATALOGS
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

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np((USER, 'dbuser', 'db user'), action=self._parse_setter(USER))
        gr_line = gr_line | np((PASSWORD, 'dbpassword', 'db password'), action=self._parse_setter(PASSWORD))
        gr_line = gr_line | np((DBSOCKET,), action=self._parse_setter(DBSOCKET))
        gr_line = gr_line | np((DBPORT,), gr_number, action=self._parse_setter(DBPORT))
        gr_line = gr_line | np((DBNAME, 'db name'), action=self._parse_setter(DBNAME))
        gr_line = gr_line | np((DBADDRESS,'db address'), action=self._parse_setter(DBADDRESS))

        gr_res = OneOrMore(gr_line)
        result = gr_res.parseString(string, parseAll=True)
        return 'Catalog: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Catalog {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.NULL_KEYS:
            if key in [ID, DIRECTOR_ID]: continue
            self._simple_phrase(key)
        return '\n'.join(self.output)

# }}}
