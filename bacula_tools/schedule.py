from . import *
from re import compile, MULTILINE, IGNORECASE, DOTALL

# Sample data:
sample1 = '''
#
# When to do the backups, full backup on first sunday of the month,
#  differential (i.e. incremental since full) every other sunday,
#  and incremental backups other days
Schedule {
  Name = "WeeklyCycle"
  Run = Full 1st sun at 23:05
  Run = Differential 2nd-5th sun at 23:05
  Run = Incremental mon-sat at 23:05
}
'''
sample2 = '''
Schedule { # This schedule does the catalog. It starts after the WeeklyCycle
  Name = "WeeklyCycleAfterBackup"
  Run = Full sun-sat at 23:10
}
'''
sample3 = '''
Schedule { # This schedule is just plain silly
  Name = "Silly Schedule";  Run = Full wed at 23:10;Run = Incremental sat at 07:00 }
'''
sample4 = '''
Schedule { # This schedule is just plain silly
  Name = None
}
'''

class Schedule(DbDict):
    def __init__(self, row={}, string=None):
        # set some default values before updating
        self[ID] = None
        self[NAME] = ''
        self[RUN] = []
        DbDict.__init__(self, row)
        if string: self.parse_string(string)
        # used to search
        self.table = SCHEDULES
        self.field = NAME
        return
    # {{{ parse_string(string): update schedule from a string (config file entry)

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        We're going to make a log of assumption here, not the least of
        which is that what will be passed in is a single Schedule{}
        resource, possibly with comments.  Anything else will throw an
        exception.  Saving wil be ... complicated.'''
        schedule_re = compile(r'^schedule\s*\{(.*)\}', MULTILINE|IGNORECASE|DOTALL)
        name_re = compile(r'^\s*name\s*=\s*(.*)', MULTILINE|IGNORECASE)
        run_re = compile(r'^\s*run\s*=\s*(.*)', MULTILINE|IGNORECASE)
        data = schedule_re.search(self._regularize_string(string)).groups()[0].strip()
        g = name_re.search(data).groups()
        self._set_name(g[0].strip())
        data = name_re.sub('', data)
        while True:
            g = run_re.search(data)
            if not g: break
            self._add_run(g.group(1))
            data = run_re.sub('', data, 1)
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
        self[ROWS] = '\n  '.join([x[1] for x in self[RUN]])
        return '''Schedule {
  Name = %(name)s
  %(rows)s
}
''' % self

# }}}
    def search(self, string):
        DbDict.search(self, string)
        return self._load_runs()

    def _load_runs(self):
        bc = Bacula_Factory()
        self[RUN] = bc.do_sql('''SELECT b.id AS id, b.data AS data FROM schedule_link a, schedule_time b
                                 WHERE a.scheduleid = %s AND a.timeid = b.id''', (self[ID],))
        return self

    def delete(self):
        bc = Bacula_Factory()
        bc.do_sql('DELETE FROM schedules WHERE id = %s', self[ID])

def testme():      # Run the testing bits!
    for t in [sample1, sample2, sample3, sample4]:
        s = Schedule(string = t)
        print(s)
    print 'testing search'
    s = Schedule()
    s.search('"WeeklyCycle"')
    print s
    print 'testing delete'
    s.delete()
    s = Schedule()
    s.search('"WeeklyCycle"')
    print s
    

