#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import * #pragma: no cover
import logging

class Job(DbDict):
    '''This actually covers both Jobs and JobDefs, EXCEPT during parsing, when
    the JobDef subclass is used because it has different default values.
    '''
    SETUP_KEYS = [
        # Enum
        TYPE, LEVEL,
        # Strings
        NOTES, ADDPREFIX, ADDSUFFIX, BASE, BOOTSTRAP, MAXIMUMBANDWIDTH, MAXSTARTDELAY,
        REGEXWHERE, RUN, SPOOLSIZE, STRIPPREFIX, VERIFYJOB, WHERE, WRITEBOOTSTRAP,
        # keys with values
        (REPLACE, 'always'), 
        # Times
        DIFFERENTIALMAXWAITTIME, IDMAXWAITTIME, INCREMENTALMAXRUNTIME, MAXRUNSCHEDTIME,
        MAXRUNTIME, MAXWAITTIME, MAXFULLINTERVAL, RESCHEDULEINTERVAL, 
        ]
    INT_KEYS = [MAXIMUMCONCURRENTJOBS, RESCHEDULETIMES, PRIORITY]
    BOOL_KEYS = [ENABLED, PREFERMOUNTEDVOLUMES, ACCURATE, ALLOWDUPLICATEJOBS,
                 ALLOWMIXEDPRIORITY, CANCELLOWERLEVELDUPLICATES,
                 CANCELQUEUEDDUPLICATES, CANCELRUNNINGDUPLICATES, JOBDEF, 
                 PREFIXLINKS, PRUNEFILES, PRUNEJOBS, PRUNEVOLUMES, RERUNFAILEDLEVELS,
                 RESCHEDULEONERROR, SPOOLATTRIBUTES, SPOOLDATA, WRITEPARTAFTERJOB
             ]
    REFERENCE_KEYS = [          # foreign keys
        DIFFERENTIALPOOL_ID, FILESET_ID, FULLPOOL_ID, CLIENT_ID,
        INCREMENTALPOOL_ID, MESSAGES_ID, POOL_ID, SCHEDULE_ID, STORAGE_ID,
        ]        
    SPECIAL_KEYS = [JOB_ID,]    # These won't be handled en- masse
    table = JOBS
    retlabel = 'Job'

    def __init__(self, row={}, string = None):
        '''Need to have a nice, clean scripts member'''
        DbDict.__init__(self, row, string)
        self.scripts = []
        return

    def __str__(self):
        '''String representation of a Job, suitable for inclusion in a Director config'''
        self.output = ['%s {' % self.retlabel,'}']
        self._simple_phrase(NAME)
        for x in self.SETUP_KEYS: self._simple_phrase(x)
        for x in self.INT_KEYS: self._simple_phrase(x)
        for x in self.REFERENCE_KEYS:
            if self[x] == None: continue
            self.output.insert(-1,'  %s = "%s"' % (x.replace('_id', '').capitalize(), self._fk_reference(x)[NAME]))
        if self[JOB_ID]: self.output.insert(-1,'  JobDefs = "%s"' % self._fk_reference(JOB_ID)[NAME])

        for x in self.BOOL_KEYS:
            if x == JOBDEF: continue
            self._yesno_phrase(x)
        for x in self.scripts: self.output.insert(-1, str(x))
        return '\n'.join(self.output)

    def _fk_reference(self, fk, string=None):
        '''This overrides the normal _fk_reference function becase we actually have
        four different keys that all point to Pools.
        '''
        key = fk.replace('_id', '')
        if 'pool' in key: key = 'pool'
        obj = bacula_tools._DISPATCHER[key]()
        if string:
            obj.search(string.strip())
            if not obj[ID]: obj._set_name(string.strip())
            if not self[fk] == obj[ID]: self._set(fk, obj[ID])
        else: obj.search(self[fk])
        return obj

    def _load_scripts(self):
        '''Job scripts are stored separately as Script objects.  This loads them in. '''
        if self[ID]:
            for row in self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s', (self[ID],), asdict=True):
                s = bacula_tools.Script({ID: row[SCRIPT_ID]})
                s.search()
                self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
                self.scripts.append(s)
        return

    def _parse_script(self, **kwargs):
        '''Helper function for parsing configuration strings.'''
        def doit(a,b,c):
            s = bacula_tools.Script(kwargs)
            s[COMMAND] = c[2]
            s.search()
            return self._add_script(s)
        return doit

    def _add_script(self, s):
        '''Add a script to the Job.'''
        self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
        self.scripts.append(s)
        row = self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (self[ID], s[ID]))
        if not row:
            self.bc.do_sql('INSERT INTO job_scripts(job_id, script_id) VALUES (%s, %s)', (self[ID], s[ID]))
        return s

    def _delete_script(self, s):
        '''Remove a Script from the Job.  This does not actually delete the Script,
        just the linkage to this job.'''
        self.bc.do_sql('DELETE FROM job_scripts WHERE id = %s', (s[ID]))
        self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
        return

    def _parse_script_full(self, *tokens):
        '''Another helper for script parsing.'''
        from pprint import pprint
        s = bacula_tools.Script()
        values = tokens[2][1]
        while values:
            k,n,v = values[:3]
            del values[:3]
            s[k.lower()] = v
        self._add_script(s.search())
        return

    def _cli_special_setup(self):
        '''Suport for adding all of the foreign-key references to the CLI.'''
        group = optparse.OptionGroup(self.parser,
                                     "Object Setters",
                                     "Various objects associated with a Job")
        group.add_option('--pool', help='Use this pool for all backups unless overridden by a more specific pool')
        group.add_option('--differential-pool', help='Use this pool for differential backups instead of the standard pool')
        group.add_option('--full-pool', help='Use this pool for full backups instead of the standard pool')
        group.add_option('--incremental-pool', help='Use this pool for incremental backups instead of the standard pool')
        group.add_option('--fileset')
        group.add_option('--client')
        group.add_option('--message-set')
        group.add_option('--schedule')
        group.add_option('--storage')
        group.add_option('--default-job', help='The job which will supply default values for those otherwise unset on this one')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''CLI Foreign Key reference actions.'''
        self._cli_deref_helper(POOL_ID, args.pool, Pool)
        self._cli_deref_helper(DIFFERENTIALPOOL_ID, args.differential_pool, Pool)
        self._cli_deref_helper(FULLPOOL_ID, args.full_pool, Pool)
        self._cli_deref_helper(INCREMENTALPOOL_ID, args.incremental_pool, Pool)

        self._cli_deref_helper(FILESET_ID, args.fileset, Fileset)
        self._cli_deref_helper(CLIENT_ID, args.client, Client)
        self._cli_deref_helper(MESSAGES_ID, args.message_set, Messages)
        self._cli_deref_helper(SCHEDULE_ID, args.schedule, Schedule)
        self._cli_deref_helper(STORAGE_ID, args.storage, Storage)
        self._cli_deref_helper(JOB_ID, args.default_job, JobDef)
        return

    def _cli_deref_helper(self, key, value, obj):
        '''Shortcut function to make _cli_special_do_parse() a lot cleaner.'''
        if value == None: return
        if value=='': return self._set(key, None)
        target = obj().search(value)
        if target[ID]: self._set(key, target[ID])
        else: print('Unable to find a match for %s, continuing' % value)
        pass


    def _cli_special_print(self):
        '''All of the foreign key objects get printed out here for the CLI.'''
        fmt = '%' + str(self._maxlen) + 's: %s'
        for x in self.REFERENCE_KEYS + self.SPECIAL_KEYS:
            if self[x] == None: continue
            print(fmt % (x.replace('_id', '').capitalize(), self._fk_reference(x)[NAME]))
        if self.scripts:
            print( '\nScripts')
            for x in self.scripts: print( x)
        return

    def _cli_special_clone(self, oid):
        '''When cloning, add in script links.'''
        select = 'SELECT %s,script_id FROM job_scripts WHERE job_id = %%s' % self[ID]
        insert = 'INSERT INTO job_scripts (job_id,script_id) VALUES (%s,%s)'
        for row in self.bc.do_sql(select, oid): self.bc.do_sql(insert, row)
        self._load_scripts()
        pass

class JobDef(Job):
    '''This is really just a Job with a different label (for printing) and a value of 1 for the JOBDEF key.'''
    retlabel = 'JobDefs'
    
    def _save(self):
        '''JobDefs force the JOBDEF key to 1 upon saving.'''
        self[JOBDEF] = 1
        return Job._save(self)

def main():
    s = Job()
    s.cli()

if __name__ == "__main__": main()
