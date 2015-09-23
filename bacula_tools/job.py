#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import bacula_tools
import logging
import optparse


class Job(bacula_tools.DbDict):

    '''This actually covers both Jobs and JobDefs, EXCEPT during parsing, when
    the JobDef subclass is used because it has different default values.
    '''
    SETUP_KEYS = [bacula_tools.TYPE, bacula_tools.LEVEL,
                  bacula_tools.NOTES, bacula_tools.ADDPREFIX, bacula_tools.ADDSUFFIX,
                  bacula_tools.BASE, bacula_tools.BOOTSTRAP,
                  bacula_tools.MAXIMUMBANDWIDTH, bacula_tools.MAXSTARTDELAY,
                  bacula_tools.REGEXWHERE, bacula_tools.RUN, bacula_tools.SPOOLSIZE,
                  bacula_tools.STRIPPREFIX, bacula_tools.VERIFYJOB,
                  bacula_tools.WHERE, bacula_tools.WRITEBOOTSTRAP,
                  (bacula_tools.REPLACE, 'always'),
                  bacula_tools.DIFFERENTIALMAXWAITTIME, bacula_tools.IDMAXWAITTIME,
                  bacula_tools.INCREMENTALMAXRUNTIME, bacula_tools.MAXRUNSCHEDTIME,
                  bacula_tools.MAXRUNTIME, bacula_tools.MAXWAITTIME,
                  bacula_tools.MAXFULLINTERVAL, bacula_tools.RESCHEDULEINTERVAL, ]
    INT_KEYS = [bacula_tools.MAXIMUMCONCURRENTJOBS,
                bacula_tools.RESCHEDULETIMES, bacula_tools.PRIORITY]
    BOOL_KEYS = [bacula_tools.ENABLED, bacula_tools.PREFERMOUNTEDVOLUMES,
                 bacula_tools.ACCURATE, bacula_tools.ALLOWDUPLICATEJOBS,
                 bacula_tools.ALLOWMIXEDPRIORITY,
                 bacula_tools.CANCELLOWERLEVELDUPLICATES,
                 bacula_tools.CANCELQUEUEDDUPLICATES,
                 bacula_tools.CANCELRUNNINGDUPLICATES, bacula_tools.JOBDEF,
                 bacula_tools.PREFIXLINKS, bacula_tools.PRUNEFILES,
                 bacula_tools.PRUNEJOBS, bacula_tools.PRUNEVOLUMES,
                 bacula_tools.RERUNFAILEDLEVELS,
                 bacula_tools.RESCHEDULEONERROR,
                 bacula_tools.SPOOLATTRIBUTES, bacula_tools.SPOOLDATA,
                 bacula_tools.WRITEPARTAFTERJOB]
    REFERENCE_KEYS = [bacula_tools.DIFFERENTIALPOOL_ID,
                      bacula_tools.FILESET_ID, bacula_tools.FULLPOOL_ID,
                      bacula_tools.CLIENT_ID, bacula_tools.INCREMENTALPOOL_ID,
                      bacula_tools.MESSAGES_ID, bacula_tools.POOL_ID,
                      bacula_tools.SCHEDULE_ID, bacula_tools.STORAGE_ID, ]
    # These won't be handled en- masse
    SPECIAL_KEYS = [bacula_tools.JOB_ID, ]
    table = bacula_tools.JOBS
    retlabel = 'Job'

    def __init__(self, row={}, string=None):
        '''Need to have a nice, clean scripts member'''
        bacula_tools.DbDict.__init__(self, row, string)
        self.scripts = []
        return

    def __str__(self):
        '''String representation of a Job, suitable for inclusion in a Director config'''
        self.output = ['%s {' % self.retlabel, '}']
        self._simple_phrase(bacula_tools.NAME)
        for x in self.SETUP_KEYS:
            self._simple_phrase(x)
        for x in self.INT_KEYS:
            self._simple_phrase(x)
        for x in self.REFERENCE_KEYS:
            if self[x] == None:
                continue
            self.output.insert(-1, '  %s = "%s"' %
                               (x.replace('_id', '').capitalize(), self._fk_reference(x)[bacula_tools.NAME]))
        if self[bacula_tools.JOB_ID]:
            self.output.insert(-1, '  JobDefs = "%s"' %
                               self._fk_reference(bacula_tools.JOB_ID)[bacula_tools.NAME])

        for x in self.BOOL_KEYS:
            if x == bacula_tools.JOBDEF:
                continue
            self._yesno_phrase(x)
        for x in self.scripts:
            self.output.insert(-1, str(x))
        return '\n'.join(self.output)

    def _fk_reference(self, fk, string=None):
        '''This overrides the normal _fk_reference function becase we actually have
        four different keys that all point to Pools.
        '''
        key = fk.replace('_id', '')
        if 'pool' in key:
            key = 'pool'
        obj = bacula_tools._DISPATCHER[key]()
        if string:
            obj.search(string.strip())
            if not obj[bacula_tools.ID]:
                obj.set_name(string.strip())
            if not self[fk] == obj[bacula_tools.ID]:
                self.set(fk, obj[bacula_tools.ID])
        else:
            obj.search(self[fk])
        return obj

    def _load_scripts(self):
        '''Job scripts are stored separately as Script objects.  This loads them in. '''
        if self[bacula_tools.ID]:
            for row in self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s', (self[bacula_tools.ID],), asdict=True):
                s = bacula_tools.Script(
                    {bacula_tools.ID: row[bacula_tools.SCRIPT_ID]})
                s.search()
                self.scripts = [
                    x for x in self.scripts if not x[bacula_tools.ID] == s[bacula_tools.ID]]
                self.scripts.append(s)
        return

    def _parse_script(self, **kwargs):
        '''Helper function for parsing configuration strings.'''
        def doit(a, b, c):
            s = bacula_tools.Script(kwargs)
            s[bacula_tools.COMMAND] = c[2]
            s.search()
            return self._add_script(s)
        return doit

    def _add_script(self, s):
        '''Add a script to the Job.'''
        self.scripts = [x for x in self.scripts if not x[bacula_tools.ID]
                        == s[bacula_tools.ID]]
        self.scripts.append(s)
        row = self.bc.do_sql(
            'SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (self[bacula_tools.ID], s[bacula_tools.ID]))
        if not row:
            self.bc.do_sql(
                'INSERT INTO job_scripts(job_id, script_id) VALUES (%s, %s)', (self[bacula_tools.ID], s[bacula_tools.ID]))
        return s

    def _delete_script(self, s):
        '''Remove a Script from the Job.  This does not actually delete the Script,
        just the linkage to this job.'''
        self.bc.do_sql(
            'DELETE FROM job_scripts WHERE id = %s', (s[bacula_tools.ID]))
        self.scripts = [
            x for x in self.scripts if not x[bacula_tools.ID] == s[bacula_tools.ID]]
        return

    def _parse_script_full(self, *tokens):
        '''Another helper for script parsing.'''
        from pprint import pprint
        s = bacula_tools.Script()
        values = tokens[2][1]
        while values:
            k, n, v = values[:3]
            del values[:3]
            s[k.lower()] = v
        self._add_script(s.search())
        return

    def _cli_special_setup(self):
        '''Suport for adding all of the foreign-key references to the CLI.'''
        group = optparse.OptionGroup(self.parser,
                                     "Object Setters",
                                     "Various objects associated with a Job")
        group.add_option(
            '--pool', help='Use this pool for all backups unless overridden by a more specific pool')
        group.add_option(
            '--differential-pool', help='Use this pool for differential backups instead of the standard pool')
        group.add_option(
            '--full-pool', help='Use this pool for full backups instead of the standard pool')
        group.add_option(
            '--incremental-pool', help='Use this pool for incremental backups instead of the standard pool')
        group.add_option('--fileset')
        group.add_option('--client')
        group.add_option('--message-set')
        group.add_option('--schedule')
        group.add_option('--storage')
        group.add_option(
            '--default-job', help='The job which will supply default values for those otherwise unset on this one')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''CLI Foreign Key reference actions.'''
        self._cli_deref_helper(
            bacula_tools.POOL_ID, args.pool, bacula_tools.Pool)
        self._cli_deref_helper(
            bacula_tools.DIFFERENTIALPOOL_ID, args.differential_pool, bacula_tools.Pool)
        self._cli_deref_helper(
            bacula_tools.FULLPOOL_ID, args.full_pool, bacula_tools.Pool)
        self._cli_deref_helper(
            bacula_tools.INCREMENTALPOOL_ID, args.incremental_pool, bacula_tools.Pool)

        self._cli_deref_helper(
            bacula_tools.FILESET_ID, args.fileset, bacula_tools.Fileset)
        self._cli_deref_helper(
            bacula_tools.CLIENT_ID, args.client, bacula_tools.Client)
        self._cli_deref_helper(
            bacula_tools.MESSAGES_ID, args.message_set, bacula_tools.Messages)
        self._cli_deref_helper(
            bacula_tools.SCHEDULE_ID, args.schedule, bacula_tools.Schedule)
        self._cli_deref_helper(
            bacula_tools.STORAGE_ID, args.storage, bacula_tools.Storage)
        self._cli_deref_helper(
            bacula_tools.JOB_ID, args.default_job, bacula_tools.JobDef)
        return

    def _cli_deref_helper(self, key, value, obj):
        '''Shortcut function to make _cli_special_do_parse() a lot cleaner.'''
        if value == None:
            return
        if value == '':
            return self.set(key, None)
        target = obj().search(value)
        if target[bacula_tools.ID]:
            self.set(key, target[bacula_tools.ID])
        else:
            print('Unable to find a match for %s, continuing' % value)
        pass

    def _cli_special_print(self):
        '''All of the foreign key objects get printed out here for the CLI.'''
        fmt = '%' + str(self._maxlen) + 's: %s'
        for x in self.REFERENCE_KEYS + self.SPECIAL_KEYS:
            if self[x] == None:
                continue
            print(
                fmt % (x.replace('_id', '').capitalize(), self._fk_reference(x)[bacula_tools.NAME]))
        if self.scripts:
            print('\nScripts')
            for x in self.scripts:
                print(x)
        return

    def _cli_special_clone(self, oid):
        '''When cloning, add in script links.'''
        select = 'SELECT %s,script_id FROM job_scripts WHERE job_id = %%s' % self[
            bacula_tools.ID]
        insert = 'INSERT INTO job_scripts (job_id,script_id) VALUES (%s,%s)'
        for row in self.bc.do_sql(select, oid):
            self.bc.do_sql(insert, row)
        self._load_scripts()
        pass


class JobDef(Job):

    '''This is really just a Job with a different label (for printing) and a value of 1 for the JOBDEF key.'''
    retlabel = 'JobDefs'

    def _save(self):
        '''JobDefs force the JOBDEF key to 1 upon saving.'''
        self[bacula_tools.JOBDEF] = 1
        return Job._save(self)


def main():
    s = Job()
    s.cli()

if __name__ == "__main__":
    main()
