#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (DATA, DbDict, ID, SCHEDULE, SCHEDULE_TIME, SCHEDULES)
import optparse


class Schedule(DbDict):
    table = SCHEDULES

    def __init__(self, row={}, string=None):
        '''Overrides DbDice.__init__ to ensure each instance has a clean entries member.'''
        DbDict.__init__(self, row, string)
        self.entries = []
        return

    def _add_run(self, run):
        '''Add a schedule line for when jobs should run.'''
        new_run = self.bc.value_ensure(SCHEDULE_TIME, DATA, run)[0]
        self.entries.append(new_run)
        row = self.bc.do_sql(
            'SELECT * FROM schedule_link WHERE scheduleid = %s AND timeid = %s', (self[ID], new_run[0]))
        if not row:
            self.bc.do_sql(
                'INSERT INTO schedule_link(scheduleid, timeid) VALUES (%s, %s)', (self[ID], new_run[0]))
        return

    def _delete_run(self, run):
        '''Unlink a run line from this Schedule.  Does not remove unused lines from the database.'''
        for row in self.entries:
            if not row[1] == run:
                continue
            self.bc.do_sql(
                'DELETE FROM schedule_link WHERE scheduleid = %s AND timeid = %s', (self[ID], row[0]))
            self.entries.remove(row)
            return
        print('I cannot delete Run entries that do not exist!')
        return

    def __str__(self):
        '''String representation of a Schedule suitable for inclustion in a config file.'''
        self.output = ['''Schedule {\n  Name = "%(name)s"''' % self, '}']
        [self.output.insert(-1, '  Run = %s' % x[1]) for x in self.entries]
        return '\n'.join(self.output)

    def _load_runs(self):
        '''When instantiating a Schedule, load all of the associated runs.'''
        if not self[ID]:
            return
        self.entries = list(self.bc.do_sql('''SELECT b.id AS id, b.data AS data FROM schedule_link a, schedule_time b
                                           WHERE a.scheduleid = %s AND a.timeid = b.id''', (self[ID],)))
        return self

    def _cli_special_setup(self):
        '''Add CLI options for adding and removing run lines.'''
        group = optparse.OptionGroup(self.parser,
                                     "Stanzas",
                                     "Add or remove time windows from the schedule")
        group.add_option(
            '--add', action='append', default=[], help='Add a time')
        group.add_option(
            '--remove', action='append', default=[], help='Removes a time')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''Actually handle CLI options for adding and removing runs.'''
        for stanza in args.add:
            self._add_run(stanza)
        for stanza in args.remove:
            self._delete_run(stanza)
        return

    def _cli_special_print(self):
        '''Print out the run lines for the CLI.'''
        print('Run times:')
        fmt = '	%s'
        [print(fmt % x[1]) for x in self.entries]

    def _cli_special_clone(self, oid):
        '''Clones should start off with the same set of runs.'''
        select = 'SELECT %s,timeid FROM schedule_link WHERE scheduleid = %%s' % self[
            ID]
        insert = 'INSERT INTO schedule_link (scheduleid,timeid) VALUES (%s,%s)'
        for row in self.bc.do_sql(select, oid):
            self.bc.do_sql(insert, row)
        self._load_runs()
        return


def main():
    s = Schedule()
    s.cli()

if __name__ == "__main__":
    main()
