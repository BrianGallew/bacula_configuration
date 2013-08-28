from __future__ import print_function
from . import *

class Script(DbDict):
    NULL_KEYS = [COMMAND, CONSOLE]
    SETUP_KEYS = [(RUNSWHEN, 'Never'),]
    TRUE_KEYS = [(RUNSONSUCCESS, 1), (RUNSONCLIENT, 1), (FAILJOBONERROR, 1)]
    FALSE_KEYS = [(RUNSONFAILURE, 0),]
    table = SCRIPTS
    prefix = '    '
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['  RunScript {  # Script ID: %d' % self[ID],'  }']
        for key in self.NULL_KEYS: self._simple_phrase(key)
        for key in self.SETUP_KEYS: self._simple_phrase(key[0])
        for key in self.TRUE_KEYS: self._yesno_phrase(key[0], onlyfalse=True)
        for key in self.FALSE_KEYS: self._yesno_phrase(key[0], onlytrue=True)
        return '\n'.join(self.output)

    # }}}
    # {{{ search():

    def search(self):
        conditions = []
        values = [self[ID],]
        sql = 'select * from %s where id = %%s' % self.table
        if not self[ID]:
            values = []
            for key in self.NULL_KEYS + [x[0] for x in self.SETUP_KEYS]:
                if not self[key] == None:
                    conditions.append('`%s` = %%s' % key)
                    values.append(self[key])
            sql = 'select * from %s where %s' % (self.table, ' and '.join(conditions))
            values = tuple(values)
        new_me = self.bc.do_sql(sql, values, asdict=True)
        if not new_me: self._create()
        else: self.update(new_me[0])
        return self

    # }}}
    # {{{ _create():

    def _create(self):
        keys = []
        keysub=[]
        values = []
        for key in self.NULL_KEYS + [x[0] for x in self.SETUP_KEYS]:
            if not self[key] == None:
                keys.append('`%s`' % key)
                keysub.append('%s')
                values.append(self[key])
        sql = 'insert into %s (%s) values (%s)' % (self.table, ','.join(keys), ','.join(keysub))
        self.bc.do_sql(sql, tuple(values), asdict=True)
        return self.search()

    # }}}
