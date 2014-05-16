#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import * #pragma: no cover
import logging

class Catalog(DbDict):
    SETUP_KEYS = [DBADDRESS, DBNAME, DBPORT, DBSOCKET, PASSWORD, USER]
    SPECIAL_KEYS = [DIRECTOR_ID,]
    table = CATALOGS

    def __str__(self):
        '''Convert a Catalog into its string representation.  The result can be
        inserted directly into the configuration of the director.'''
        self.output = ['Catalog {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        return '\n'.join(self.output)

    def search(self, key=None):
        '''Override the standard self.search() function to look up a catalog by
        Director ID.  This is primarily used when generating the
        configuration for a director, as you'll have a Director ID and need
        to look up the associated catalog.'''
        DbDict.search(self, key)
        if self[ID]: return self
        if not self[DIRECTOR_ID]: return self # can't look myself up if I don't have any attributes
        new_me = self.bc.value_check(self.table, DIRECTOR_ID, self[DIRECTOR_ID], asdict=True)
        try: self.update(new_me[0])
        except Exception as e: pass
        [getattr(self, x)() for x in dir(self) if '_load_' in x]
        return self

    def _cli_special_setup(self):
        self.parser.add_option('--director', help='The name or ID of the Director that uses this catalog')
        return

    def _cli_special_do_parse(self, args):
        '''It should be noted that a Catalog can be associated with one, and only
        one, Director.  This function handles changing the Director from the CLI.'''
        if args.director == None: return # Nothing to do!
        d = bacula_tools.Director()
        d.search(args.director)
        if not d[ID]: d.search(args.director)
        if not d[ID]:
            print('\n***WARNING***: Unable to find a director using "%s".  Association not changed\n' % args.director)
            return
        self.set(DIRECTOR_ID, d[ID])
        return

    def _cli_special_print(self):
        '''De-reference the Director and print its name.'''
        d = bacula_tools.Director().search(self[DIRECTOR_ID])
        fmt = '%' + str(self._maxlen) +'s: %s'
        print(fmt % (DIRECTOR, d[NAME]))
        return

    def connect(self):
        c_conn = Bacula_Config()
        args = []
        for key in [DBNAME, USER, PASSWORD, DBADDRESS]:
            value = self[key]
            if value == None: value = ''
            args.append(value)
        c_conn.connect(*args)
        return c_conn

# Implement the CLI for managing Catalogs
def main():
    s = Catalog()
    s.cli()

if __name__ == "__main__": main()
