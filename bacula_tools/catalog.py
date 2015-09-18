#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''Catalog management
'''

from __future__ import print_function, absolute_import
import bacula_tools
import logging
logger = logging.getLogger(__name__)


class Catalog(bacula_tools.DbDict):

    '''Bacula Catalog object
    '''
    SETUP_KEYS = [bacula_tools.DBADDRESS, bacula_tools.DBNAME, bacula_tools.DBPORT,
                  bacula_tools.DBSOCKET, bacula_tools.PASSWORD, bacula_tools.USER]
    SPECIAL_KEYS = [bacula_tools.DIRECTOR_ID, ]
    table = bacula_tools.CATALOGS

    def __str__(self):
        '''Convert a Catalog into its string representation.  The result can be
        inserted directly into the configuration of the director.'''
        self.output = ['Catalog {\n  Name = "%(name)s"' % self, '}']

        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        return '\n'.join(self.output)

    def search(self, key=None):
        '''Override the standard self.search() function to look up a catalog by
        Director ID.  This is primarily used when generating the
        configuration for a director, as you'll have a Director ID and need
        to look up the associated catalog.'''
        bacula_tools.DbDict.search(self, key)
        if self[bacula_tools.ID]:
            return self
        if not self[bacula_tools.DIRECTOR_ID]:
            return self  # can't look myself up if I don't have any attributes
        new_me = self.bc.value_check(
            self.table, bacula_tools.DIRECTOR_ID, self[bacula_tools.DIRECTOR_ID], asdict=True)
        try:
            self.update(new_me[0])
        except Exception as the_exception:
            logger.debug(str(the_exception))
        for x in dir(self):
            if '_load_' in x:
                getattr(self, x)()
        return self

    def _cli_special_setup(self):
        self.parser.add_option(
            '--director', help='The name or ID of the Director that uses this catalog')
        return

    def _cli_special_do_parse(self, args):
        '''It should be noted that a Catalog can be associated with one, and only
        one, Director.  This function handles changing the Director from the CLI.'''
        if args.director == None:
            return  # Nothing to do!
        the_director = bacula_tools.Director()
        the_director.search(args.director)
        if not the_director[bacula_tools.ID]:
            the_director.search(args.director)
        if not the_director[bacula_tools.ID]:
            logger.warning(
                'Unable to find a director using "%s".  Association not changed',
                args.director)
            return
        self.set(bacula_tools.DIRECTOR_ID, the_director[bacula_tools.ID])
        return

    def _cli_special_print(self):
        '''De-reference the Director and print its name.'''
        the_director = bacula_tools.Director().search(
            self[bacula_tools.DIRECTOR_ID])
        fmt = '%' + str(self._maxlen) + 's: %s'
        print(fmt % (bacula_tools.DIRECTOR, the_director[bacula_tools.NAME]))
        return

    def connect(self):
        '''Connect to the correct director
        '''
        c_conn = bacula_tools.Bacula_Config()
        args = []
        for key in [bacula_tools.DBNAME, bacula_tools.USER,
                    bacula_tools.PASSWORD, bacula_tools.DBADDRESS]:
            value = self[key]
            if value == None:
                value = ''
            args.append(value)
        c_conn.connect(*args)
        return c_conn

# Implement the CLI for managing Catalogs
def main():
    s = Catalog()
    s.cli()


if __name__ == "__main__":
    main()
