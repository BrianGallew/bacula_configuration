from . import *
from pprint import pprint

class Messages(DbDict):
    table = MESSAGES
    # {{{ __str__(): 

    def __str__(self):
        output = 'Messages {\n  Name = "%(name)s"\n  %(data)s\n}' % self
        return output

# }}}
