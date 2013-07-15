'''Bacula configuration database stuff: common routines, credentials, etc'''
# Bacula_Config and BSock classes and various definitions used by Bacula python programs.

import MySQLdb as db
import MySQLdb.cursors
import os, sys

from . import *

_singleton = None
def Bacula_Factory():
    global _singleton
    if not _singleton: _singleton = Bacula_Config()
    return _singleton

class Bacula_Config:
    '''Class that wraps up lots of dealings with the configuration
    database.  Generally speaking, you should call Bacula_Factory instead
    of instantiating this directly, as the singleton is really good about
    re-using information.
    '''
    # {{{ Various class constants

    DEBUG = 0
    CONNECTIONS = {}
    CURRENT_CONNECTION = None
    BOOTSTRAPDIR = "/var/db/bacula"
    directors = []
    storage_daemons = []
    clients = []
    MULTIPLIERS = {             # Cheating on time calculations!
        'week': 7,
        'weeks': 7,
        'month': 30,
        'months': 30,
        'day': 1,
        'days': 1,
        'year': 365,
        'years': 365,
        }

    # }}}
    # {{{ db_connect(database=DBSCHEMA, user=DBUSER, passwd=DBPASSWORD, host=DBHOST):

    def db_connect(self, database=DBSCHEMA, user=DBUSER, passwd=DBPASSWORD, host=DBHOST):
        '''Use the alt flag to get a one-off DB connection'''
        key = database+user+passwd+host
        if not self.CONNECTIONS.has_key(key): 
            self.CONNECTIONS[key] = db.connect(db = database, user = user, passwd = passwd, host = host)
        self.CURRENT_CONNECTION = self.CONNECTIONS[key]
        self.CURRENT_CONNECTION.autocommit(True)
        return self.CONNECTIONS[key]

    # }}}
    # {{{ connect_bacula(): Connect to the bacula database

    def connect_bacula(self):
        for d in self.get_directors():
            if d[PRIMARY_DIR]:
                return self.db_connect(database=d[DBNAME], user=d[DBUSER], passwd=d[DBPASSWORD], host=d[DBADDRESS])
        return

    # }}}
    # {{{ get_cursor():

    def get_cursor(self, **kwargs):
        if not self.CURRENT_CONNECTION: self.db_connect() # Assume default connection stuff
        return self.CURRENT_CONNECTION.cursor(**kwargs)

    # }}}
    # {{{ get_column(column, where_phrase = None, where_args = None, distinct=False, order = None, dbtable = HOSTS):

    def get_column(self, column, where_phrase = None, where_args = None, distinct=False, order = None, dbtable = HOSTS):
        cursor = self.get_cursor()
        if not order: order = column
        wp = 'WHERE %s' % where_phrase if where_phrase else ''
        dt = 'DISTINCT' if distinct else ''
        sql = 'SELECT %(dt)s %(column)s FROM %(dbtable)s %(wp)s ORDER BY %(column)s' % locals()
        cursor.execute(sql, where_args)
        return [x[0] for x in cursor.fetchall()]

    # }}}
    # {{{ do_sql(sql, args=None):

    def do_sql(self, sql, args=None, asdict=False):
        if asdict: cursor = self.get_cursor(cursorclass=db.cursors.DictCursor)
        else: cursor = self.get_cursor()
        cursor.execute(sql, args)
        return cursor.fetchall()

    # }}}
    # {{{ safe_do_sql(sql, args=None):

    def safe_do_sql(self, sql, args=None):
        try:
            return self.do_sql(sql, args)
        except Exception, e:
            (errno, string) = eval(str(e))
            if errno == 1142: self.die('%s is not allowed to do that' % os.uname()[1])
            self.die(str(e))

    # }}}
    # {{{ formatted_query_result(sql, prefix = '', infix = '', suffix = '', *selector, **kwargs):

    def formatted_query_result(self, sql, prefix = '', infix = '', suffix = '', *selector, **kwargs):
        '''This basically allows us to pull an annoying query-and-format into a neat little function.

        WARNING: any variables that will be handled by the selector must be
        protected against interpolation (e.g. %s -> %%s)
        '''
        locals().update(kwargs)   # This trick allows arbitrary expansion of our locals
        sql = sql % locals()

        result = self.do_sql(sql, selector)

        if not result: return ''                # Nothing!
        return prefix + infix.join([x[0] or '' for x in result if x]) + suffix

    # }}}
    # {{{ die(*msg):

    def die(self, *msg):
        print "An error occurred and %s is no longer able to continue\n" % sys.argv[0]
        print '\n'.join(msg)
        print '\n'
        exit(-1)
        return                  # This will never happen, but it makes auto-formatting a little happier.

    # }}}
    # {{{ suggest(table, field, value):

    def suggest(self, table, field, value):
        sql = "select %(field)s from %(table)s where %(field)s like %%s limit 5" % locals()
        mangled_value = '%' + value[1:-1] + '%'
        data = self.do_sql(sql, mangled_value)
        if data:                # OK, we got some partial matches
            return "Possible matches for '%s':\n\t" % value + '\n\t'.join([x[0] for x in data if x])
        return "I was unable to find any close matches to '%(value)s'.  Please try harder.\n" % locals();

    # }}}
    # {{{ value_check(table, field, value, suggest=False, asdict=False):

    def value_check(self, table, field, value, suggest=False, asdict=False):
        '''check the existence of a value in a column'''
        result = self.do_sql("SELECT * FROM %(table)s where %(field)s = %%s" % locals(), value, asdict);
        if result: return result
        if not suggest: return result
        return self.die('No such value (%(value)s) in %(table)s' % locals(),
                        '',
                        self.suggest(table, field, value))

    # }}}
    # {{{ value_ensure(table, field, value):

    def value_ensure(self, table, field, value):
        '''ensure the existence of a value in a column'''
        if not self.value_check(table, field, value):
            self.safe_do_sql("INSERT INTO %(table)s (%(field)s) VALUES (%%s)" % locals(), value);
        return self.value_check(table, field, value)

    # }}}
    # {{{ dump_schedule(name):

    def dump_schedule(self, name):
        '''Returns the named schedule as a nicely formatted string'''
        sql = '''
    SELECT 
        f.data AS name
    FROM
        bacula_schedules AS s
            LEFT JOIN
        bacula_schedule_pivot AS g ON s.scheduleid = g.scheduleid
            INNER JOIN
        bacula_schedule_time AS f ON g.timeid = f.timeid
            AND s.name = %%s
    ORDER BY f.data
    '''
        data = self.formatted_query_result(sql, "  Run  = ", "\n  Run  = ", "\n", name)
        return '''Schedule {\n  Name = "%(name)s"\n%(data)s}\n\n''' % locals()

    # }}}
    # {{{ dump_all_schedules():

    def dump_all_schedules(self):
        return ''.join([self.dump_schedule(x) for x in self.get_column('schedule', distinct = True)])

    # }}}
    # {{{ dump_fileset(fsname):

    def dump_fileset(self, fsname):
        '''Returns the named fileset as a nicely formatted string'''
        sql = '''SELECT f.name AS name FROM filesets AS s
                 LEFT JOIN fileset_%(part)ss AS g ON s.id = g.fileset_id AND g.exclude=%%s
                 INNER JOIN %(part)ss AS f ON g.%(part)s_id = f.id AND s.name = %%s ORDER BY f.name'''
        fp = "    File = "
        op = "    Options {\n      "
        in_file = self.formatted_query_result(sql, fp, "\n" + fp,  "\n",        0, fsname, part='file')
        ex_file = self.formatted_query_result(sql, fp, "\n" + fp,  "\n",        1, fsname, part='file')
        in_opt  = self.formatted_query_result(sql, op, "\n      ", "\n    }\n", 0, fsname, part='option')
        ex_opt  = self.formatted_query_result(sql, op, "\n      ", "\n    }\n", 1, fsname, part='option')
        return '''FileSet {\n  Name = "%(fsname)s"\n  Include {\n%(in_file)s%(in_opt)s  }\n\n  Exclude {\n%(ex_file)s%(ex_opt)s  }\n}\n\n''' % locals()

    # }}}
    # {{{ dump_all_filesets():

    def dump_all_filesets(self):
        return ''.join([self.dump_fileset(x) for x in self.get_column('fileset', distinct = True)])

    # }}}
    # {{{ get_dict_data(sql, targetclass = None, *args):

    ### FIXME: this function should go away once the other objects become more "real".
    def get_dict_data(self, sql, targetclass, *args):
        dlist = []
        for row in self.do_sql(sql, args, True):
            if targetclass:
                dlist.append(targetclass(row, *args))
            else:
                dlist.append(row)
        return dlist

    # }}}
    # {{{ get_directors():

    def get_directors(self):
        if not self.directors:
            self.directors = self.get_dict_data('SELECT * FROM bacula_directors', Director)
        return self.directors

    # }}}
    # {{{ get_storage_daemons():

    def get_storage_daemons(self):
        if not self.storage_daemons:
            ts = self.get_timespan()
            d = self.get_directors()
            self.storage_daemons = self.get_dict_data('''SELECT * FROM bacula_hosts
                                                         WHERE hostname IN (SELECT DISTINCT storageserver
                                                                            FROM bacula_hosts) ORDER BY hostname''',
                                                      StorageDaemon, ts, d)
        return self.storage_daemons

# }}}
    # {{{ get_clients(specific=None):

    def get_clients(self, specific=None):
        '''Always returns a list'''
        if specific:
            if self.clients:
                c = [x for x in self.clients if x[HOSTNAME] == specific]
                if c: return c
            return self.get_dict_data("SELECT * FROM bacula_hosts WHERE hostname = '%s'" % specific, Client)
        if not self.clients:
            self.clients = self.get_dict_data('SELECT * FROM bacula_hosts order by hostname desc', Client)
        return self.clients

    # }}}
    # {{{ get_timespan(): Convert to days 

    def get_timespan(self):
        sql = '''
SELECT DISTINCT file_retention AS retention
FROM bacula_hosts
    UNION
SELECT DISTINCT job_retention AS retention
FROM bacula_hosts'''
        most_days = 7           # Minimum of 7 days
        for row in self.do_sql(sql):
            parts = row[0].split(None, 1)
            if len(parts) == 1: new_days = int(parts[0])
            else: new_days = int(parts[0]) * self.MULTIPLIERS[parts[1]]
            if new_days > most_days: most_days = new_days
        return '%d days' % most_days

# }}}
