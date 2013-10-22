from __future__ import print_function
from . import *

class Messages(DbDict):
    SETUP_KEYS = [(NAME, ''), (DATA, '')]
    table = MESSAGES
    _select = 'SELECT * FROM messages_link where messages_id = %s and link_type = %s'
    _insert = 'INSERT INTO messages_link (messages_id, ref_id, link_type) values (%s, %s, %s)'
    def parse_string(self, string, obj=None):
        retval = DbDict.parse_string(self, string)
        if obj: self.link(obj)
        return retval

    def link(self, obj):
        try:
            self.bc.do_sql(self._insert, (self[ID], obj[ID], obj.IDTAG))
        except Exception as e:
            if e.args[0] == 1062: pass # 1062 is what happens when you try to insert a duplicate row
            else:
                print(e)
                raise

        
    # {{{ __str__(): 

    def __str__(self):
        output = 'Messages {\n  Name = "%(name)s"\n  %(data)s\n}' % self
        return output

# }}}
