from . import *
from re import compile, MULTILINE, IGNORECASE, DOTALL

class Schedule(DbDict):
    # {{{ __init__(row={}, string=None):

    def __init__(self, row={}, string=None):
        # set some default values before updating
        self[ID] = None
        self[NAME] = ''
        self[RUN] = []
        DbDict.__init__(self, row)
        if string: self.parse_string(string)
        # used to search
        self.table = SCHEDULES
        return

    # }}}
    # {{{ parse_string(string): update schedule from a string (config file entry)

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        We're going to make a log of assumption here, not the least of
        which is that what will be passed in is a single Schedule{}
        resource, without comments.  Anything else will throw an
        exception.'''
        run_re = compile(r'^\s*run\s*=\s*(.*)', MULTILINE|IGNORECASE)
        data = string.strip()
        g = self.name_re.search(data).groups()
        s = g[0].strip()
        if s[0] == '"' and  s[-1] == '"': s = s[1:-1]
        if s[0] == "'" and  s[-1] == "'": s = s[1:-1]
        self._set_name(s)
        data = self.name_re.sub('', data)
        while True:
            g = run_re.search(data)
            if not g: break
            s = g.group(1).strip()
            if s[0] == '"' and  s[-1] == '"': s = s[1:-1]
            if s[0] == "'" and  s[-1] == "'": s = s[1:-1]
            self._add_run(s)
            data = run_re.sub('', data, 1)
        print "Schedule:", self[NAME]
        return

    # }}}
    # {{{ _add_run(run): add another run

    def _add_run(self, run):
        bc = Bacula_Factory()
        new_run = bc.value_ensure(SCHEDULE_TIME, DATA, run)[0]
        self[RUN].append(new_run)
        row = bc.do_sql('SELECT * FROM schedule_link WHERE scheduleid = %s AND timeid = %s', (self[ID], new_run[0]))
        if not row:
            bc.do_sql('INSERT INTO schedule_link(scheduleid, timeid) VALUES (%s, %s)', (self[ID], new_run[0]))

        return

    # }}}
    # {{{ _delete_run(run): add another run

    def _delete_run(self, run):
        bc = Bacula_Factory()
        for row in self[RUN]:
            if not row[1] == run: continue
            bc.do_sql('DELETE FROM schedule_link WHERE scheduleid = %s AND timeid = %s', (self[ID], row[0]))
            self[RUN].remove(row)
            return
        print 'I cannot delete Run entries that do not exist!'
        return

    # }}}
    # {{{ _set_name(name): set my name

    def _set_name(self, name):
        bc = Bacula_Factory()
        row = bc.value_ensure(SCHEDULES, NAME, name)
        self[NAME] = row[0][1]
        self[ID] = row[0][0]
        return

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self[ROWS] = '\n'.join(['  Run = %s' % x[1] for x in self[RUN]])
        return '''Schedule {\n  Name = %(name)s\n%(rows)s\n}\n''' % self

# }}}
    # {{{ search(string): load information based on a name

    def search(self, string):
        DbDict.search(self, string)
        return self._load_runs()

    # }}}
    # {{{ _load_runs(): helper for loading self from the database

    def _load_runs(self):
        bc = Bacula_Factory()
        self[RUN] = list(bc.do_sql('''SELECT b.id AS id, b.data AS data FROM schedule_link a, schedule_time b
                                      WHERE a.scheduleid = %s AND a.timeid = b.id''', (self[ID],)))
        return self

    # }}}
    

