from __future__ import print_function
from . import *

class Script(DbDict):
    NULL_KEYS = [ID, COMMAND, CONSOLE]
    SETUP_KEYS = [(RUNSONSUCCESS, 1), (RUNSONFAILURE, 0), (RUNSONCLIENT, 1), (FAILJOBONERROR, 1), (RUNSWHEN, 'Never')]
    table = SCRIPTS
    prefix = '    '
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['  RunScript {','  }']
        self._simple_phrase(COMMAND)
        self._simple_phrase(CONSOLE)
        self._simple_phrase(RUNSWHEN)
        self._yesno_phrase(RUNSONSUCCESS, onlyfalse=True)
        self._yesno_phrase(RUNSONCLIENT, onlyfalse=True)
        self._yesno_phrase(FAILJOBONERROR, onlyfalse=True)
        self._yesno_phrase(RUNSONFAILURE, onlytrue=True)
        return '\n'.join(self.output)

    # }}}
    # {{{ search():

    def search(self):
        conditions = []
        values = []
        for key in self.NULL_KEYS + [x[0] for x in self.SETUP_KEYS]:
            if not self[key] == None:
                conditions.append('`%s` = %%s' % key)
                values.append(self[key])
        sql = 'select * from %s where %s' % (self.table, ' and '.join(conditions))
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
