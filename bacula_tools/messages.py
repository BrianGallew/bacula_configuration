from . import *

class Messages(DbDict):
    SETUP_KEYS = [(NAME, ''), (DATA, '')]
    table = MESSAGES
    # {{{ __str__(): 

    def __str__(self):
        output = 'Messages {\n  Name = "%(name)s"\n  %(data)s\n}' % self
        return output

# }}}
