#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (COMMAND, CONSOLE, DbDict, FAILJOBONERROR, ID,
                          NAME, RUNSONCLIENT, RUNSONFAILURE,
                          RUNSONSUCCESS, RUNSWHEN, SCHEDULES, SCRIPTS,
                          )
import logging


class Script(DbDict):

    '''This is a "ninja" class.  There are no Script resources in Bacula, but there should be.

    Scripts handle the RunScript items in Jobs.
    '''
    SETUP_KEYS = [
        (RUNSWHEN, 'Never', 'Legal values are "Never", "Before", "After", "AfterVSS", and "Always"'), COMMAND, CONSOLE]
    BOOL_KEYS = [RUNSONSUCCESS, RUNSONCLIENT, FAILJOBONERROR, RUNSONFAILURE, ]
    table = SCRIPTS
    prefix = '    '

    def __str__(self):
        '''Standardized string representation of a Script, suitable for including in a Job configuration.'''
        self.output = [
            '  RunScript {  # Script ID: %d\n    # Name: %s' % (self[ID], self[NAME]), '  }']
        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        for key in self.BOOL_KEYS:
            self._yesno_phrase(key)
        return '\n'.join(self.output)

    def search(self, key=None):
        '''Since Scripts are ninjas, they have no Name=FOO in the configuration
        file.  We will generate names upon creation, and use them, but we have to
        support much more complicated searching to deal with the reality of Bacula
        configurations.'''
        logging.debug('dbdict search')
        DbDict.search(self, key)
        if self[ID]:
            return self
        logging.debug('continuing search')
        conditions = []
        values = []
        for key in self.keys():
            if not self[key] == None:
                conditions.append('`%s` = %%s' % key)
                values.append(self[key])
        sql = 'select * from %s where %s' % (self.table,
                                             ' and '.join(conditions))
        values = tuple(values)

        new_me = self.bc.do_sql(sql, values, asdict=True)
        if not new_me:
            self._create()
        else:
            self.update(new_me[0])
        return self

    def _create(self):
        '''This is where new Scripts get created and named.'''
        keys = []
        keysub = []
        values = []
        for key in self.keys():
            if not self[key] == None:
                keys.append('`%s`' % key)
                keysub.append('%s')
                values.append(self[key])
        sql = 'insert into %s (%s) values (%s)' % (
            self.table, ','.join(keys), ','.join(keysub))
        self.bc.do_sql(sql, tuple(values), asdict=True)
        self.search()
        self[NAME] = 'Script: %d' % self[ID]
        self._save()
        return self


def main():
    s = Script()
    s.cli()

if __name__ == "__main__":
    main()
