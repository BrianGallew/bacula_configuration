'''Bacula configuration database stuff: common routines, credentials, etc'''
# Bacula_Config and BSock classes and various definitions used by Bacula python programs.

import MySQLdb as db
import MySQLdb.cursors
import os, sys

from . import *

_singleton = None
def Bacula_Factory():
    '''Returns a singleton instance of the Bacula_Config class.  This is a
    simple optimization to reduce the number of database connections used.'''
    global _singleton
    if not _singleton: _singleton = Bacula_Config()
    return _singleton

class Bacula_Config:
    '''Class that wraps up lots of dealings with the configuration database.
    You probably should call Bacula_Factory instead of instantiating this
    directly.

    '''
    # {{{ Various class constants

    CONNECTIONS = {}            # array of connections to the database
    CURRENT_CONNECTION = None   # The currently in-use connection

    # }}}
    # {{{ __db_connect(database=MYSQL_DB, user=MYSQL_USER, passwd=MYSQL_PASS, host=MYSQL_HOST):

    def __db_connect(self, database=MYSQL_DB, user=MYSQL_USER, passwd=MYSQL_PASS, host=MYSQL_HOST):
        '''Connect to the database.  Tries to look up an existing connection to use if possible'''
        key = database+user+passwd+host
        if not self.CONNECTIONS.has_key(key): 
            self.CONNECTIONS[key] = db.connect(db = database, user = user, passwd = passwd, host = host)
        self.CURRENT_CONNECTION = self.CONNECTIONS[key]
        self.CURRENT_CONNECTION.autocommit(True)
        return self.CONNECTIONS[key]

    # }}}
    # {{{ get_cursor():

    def get_cursor(self, **kwargs):
        '''Returns a cursor for querying.  Will automatically connect to the database if necessary.'''
        if not self.CURRENT_CONNECTION: self.__db_connect() # Assume default connection stuff
        return self.CURRENT_CONNECTION.cursor(**kwargs)

    # }}}
    # {{{ do_sql(sql, args=None):

    def do_sql(self, sql, args=None, asdict=False):
        '''A general-purpose SQL query function.  It handles acquiring a cursor
        that returns either a list (default) or dictionary as requested,
        performs the sql, and returns the entire resultset.

        You should not use this for extremely large resultsets.'''
        if asdict: cursor = self.get_cursor(cursorclass=db.cursors.DictCursor)
        else: cursor = self.get_cursor()
        cursor.execute(sql, args)
        return cursor.fetchall()

    # }}}
    # {{{ suggest(table, field, value):

    def suggest(self, table, field, value):
        '''This is an effort to be helpful in the case where you have an idea on
        the name of a resource, but you aren't really sure of the *precise*
        name.  This strips off the first and last characters of your name
        string, wraps the results in %%, and then queries the database
        (limiting the result set to 5).'''
        sql = "select %(field)s from %(table)s where %(field)s like %%s limit 5" % locals()
        mangled_value = '%' + value[1:-1] + '%'
        data = self.do_sql(sql, mangled_value)
        if data:                # OK, we got some partial matches
            return "Possible matches for '%s':\n\t" % value + '\n\t'.join([x[0] for x in data if x])
        return "I was unable to find any close matches to '%(value)s'.  Please try harder.\n" % locals();

    # }}}
    # {{{ value_check(table, field, value, suggest=False, asdict=False):

    def value_check(self, table, field, value, suggest=False, asdict=False):
        '''Check the existence of a value in a column.  If it exists, return the
        row as a dictionary, otherwise die with a suggestion of possible
        alternatives to search for.'''
        sql = "SELECT * FROM `%(table)s` where `%(field)s` = %%s" % locals()
        result = self.do_sql(sql, value, asdict);
        if result: return result
        if not suggest: return result
        return die('No such value (%(value)s) in %(table)s' % locals(),
                   '',
                   self.suggest(table, field, value))

    # }}}
    # {{{ value_ensure(table, field, value, asdict=False):

    def value_ensure(self, table, field, value, asdict=False):
        '''Ensure the existence of a value in a column.  Use this to find-or-create
        a resource record.'''
        if not self.value_check(table, field, value, asdict=asdict):
            self.do_sql("INSERT INTO %(table)s (%(field)s) VALUES (%%s)" % locals(), value);
        return self.value_check(table, field, value, asdict=asdict)

    # }}}
