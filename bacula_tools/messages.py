from . import *
from pprint import pprint

class Messages(DbDict):
    LEGAL_KEYS = []
    # {{{ __init__(row={}, string=None):

    def __init__(self, row={}, string=None):
        # set some default values before updating
        self[ID] = None
        self[NAME] = ''
        self[DATA] = ''
        DbDict.__init__(self, row)
        self.table = MESSAGES
        if string: self.parse_string(string)
        # used to search
        return

    # }}}
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        We're cheating and treating this object as a blob.
        '''
        g = self.name_re.search(string).groups()
        self._set_name(g[0].strip())
        string = self.name_re.sub('', string)
        data = '\n  '.join([x.strip() for x in string.split('\n') if x])
        self._set(DATA, data)
        print "Messages:", self[NAME]
        return

    # }}}
    # {{{ _set_name(name): set my name

    def _set_name(self, name):
        bc = Bacula_Factory()
        row = bc.value_ensure(MESSAGES, NAME, name.strip())[0]
        self[ID] = row[0]
        self[NAME] = row[1]
        self[DATA] = self[DATA] if self[DATA] else row[2]
        return

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        output = 'Messages {\n  Name = %(name)s\n  %(data)s\n}' % self
        return output

# }}}
