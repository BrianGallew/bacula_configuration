from . import *
from pprint import pprint

class Messages(DbDict):
    table = MESSAGES
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
        output = 'Messages {\n  Name = "%(name)s"\n  %(data)s\n}' % self
        return output

# }}}
