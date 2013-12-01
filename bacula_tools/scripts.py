#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Script(DbDict):
    '''This is a "ninja" class.  There are no Script resources in Bacula, but there should be.

    Scripts handle the RunScript items in Jobs.
    '''
    SETUP_KEYS = [(RUNSWHEN, 'Never', 'Legal values are "Never", "Before", "After", "AfterVSS", and "Always"'), COMMAND, CONSOLE]
    BOOL_KEYS = [RUNSONSUCCESS, RUNSONCLIENT, FAILJOBONERROR, RUNSONFAILURE,]
    table = SCRIPTS
    prefix = '    '
    # {{{ __str__(): 

    def __str__(self):
        '''Standardized string representation of a Script, suitable for including in a Job configuration.'''
        self.output = ['  RunScript {  # Script ID: %d\n    # Name: %s' % (self[ID], self[NAME]),'  }']
        for key in self.SETUP_KEYS: self._simple_phrase(key)
        for key in self.BOOL_KEYS: self._yesno_phrase(key)
        return '\n'.join(self.output)

    # }}}
    # {{{ search():

    def search(self, key=None):
        '''Since Scripts are ninjas, they have no Name=FOO in the configuration
        file.  We will generate names upon creation, and use them, but we have to
        support much more complicated searching to deal with the reality of Bacula
        configurations.'''
        debug_print('dbdict search')
        DbDict.search(self, key)
        if self[ID]: return self
        debug_print('continuing search')
        conditions = []
        values = []
        for key in self.keys():
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
        '''This is where new Scripts get created and named.'''
        keys = []
        keysub=[]
        values = []
        for key in self.keys():
            if not self[key] == None:
                keys.append('`%s`' % key)
                keysub.append('%s')
                values.append(self[key])
        sql = 'insert into %s (%s) values (%s)' % (self.table, ','.join(keys), ','.join(keysub))
        self.bc.do_sql(sql, tuple(values), asdict=True)
        self.search()
        self[NAME] = 'Script: %d' % self[ID]
        self._save()
        return self

    # }}}

def main():
    s = Script()
    s.cli()

if __name__ == "__main__": main()
