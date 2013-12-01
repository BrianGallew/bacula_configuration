#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

# These are some shortcuts I put here just to make later code look a little cleaner.
RBJ = PList('Run Before Job')
RAJ = PList('Run After Job')
RAFJ = PList( 'Run After Failed Job')
CRBJ = PList('Client Run Before Job')
CRAJ = PList('Client Run After Job')

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
    # {{{ __init__(row={}, string = None):

    def __init__(self, row={}, string = None):
        '''Need to have a nice, clean scripts member'''
        DbDict.__init__(self, row, string)
        self.scripts = []
        return

    # }}}
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        # {{{ boilerplate.  Sigh

        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        FTR: this is hideous.
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith, nums, printables, nullDebugAction
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def np(words, fn = gr_opt_quoted_string, action=nullDebugAction):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        # }}}
        # {{{ # Easy ones that go don't take embedded spaces because I say so.

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        for key in [TYPE, LEVEL, REPLACE, BASE, RUN, WHERE]:
            gr_line = gr_line | np((key,), action=self._parse_setter(key))

            # }}}
        # {{{ # Group of _id variables

        gr_line = gr_line | np(PList('differential pool'), action=self._parse_setter(DIFFERENTIALPOOL_ID))
        gr_line = gr_line | np(PList('file set'), action=self._parse_setter(FILESET_ID, dereference=True))
        gr_line = gr_line | np(PList('full pool'), action=self._parse_setter(FULLPOOL_ID))
        gr_line = gr_line | np((CLIENT,), action=self._parse_setter(CLIENT_ID, dereference=True))
        gr_line = gr_line | np(PList('incremental pool'), action=self._parse_setter(INCREMENTALPOOL_ID))
        gr_line = gr_line | np((MESSAGES,), action=self._parse_setter(MESSAGES_ID, dereference=True))
        gr_line = gr_line | np((POOL,), action=self._parse_setter(POOL_ID, dereference=True))
        gr_line = gr_line | np((SCHEDULE,), action=self._parse_setter(SCHEDULE_ID, dereference=True))
        gr_line = gr_line | np((STORAGE,), action=self._parse_setter(STORAGE_ID, dereference=True))
        gr_line = gr_line | np(PList('job defs'), action=self._parse_setter(JOB_ID, dereference=True))

        # }}}
        # {{{ # INTs

        gr_line = gr_line | np(PList('maximum concurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
        gr_line = gr_line | np(PList('re schedule times'), gr_number, action=self._parse_setter(RESCHEDULETIMES))
        gr_line = gr_line | np((PRIORITY,), gr_number, action=self._parse_setter(PRIORITY))

        # }}}
        # {{{ # True/False

        gr_line = gr_line | np((ACCURATE,), gr_yn, action=self._parse_setter(ACCURATE))
        gr_line = gr_line | np(PList('allow duplicate jobs'), gr_yn, action=self._parse_setter(ALLOWDUPLICATEJOBS))
        gr_line = gr_line | np(PList('allow mixed priority'), gr_yn, action=self._parse_setter(ALLOWMIXEDPRIORITY))
        gr_line = gr_line | np(PList('cancel lower level duplicates'), gr_yn, action=self._parse_setter(CANCELLOWERLEVELDUPLICATES))
        gr_line = gr_line | np(PList('cancel queued duplicates'), gr_yn, action=self._parse_setter(CANCELQUEUEDDUPLICATES))
        gr_line = gr_line | np(PList('cancel running duplicates'), gr_yn, action=self._parse_setter(CANCELRUNNINGDUPLICATES))
        gr_line = gr_line | np((ENABLED,), gr_yn, action=self._parse_setter(ENABLED))
        gr_line = gr_line | np(PList('prefer mounted volumes'), gr_yn, action=self._parse_setter(PREFERMOUNTEDVOLUMES))
        gr_line = gr_line | np(PList('prefix links'), gr_yn, action=self._parse_setter(PREFIXLINKS))
        gr_line = gr_line | np(PList('prune files'), gr_yn, action=self._parse_setter(PRUNEFILES))
        gr_line = gr_line | np(PList('prune jobs'), gr_yn, action=self._parse_setter(PRUNEJOBS))
        gr_line = gr_line | np(PList('prune volumes'), gr_yn, action=self._parse_setter(PRUNEVOLUMES))
        gr_line = gr_line | np(PList('re run failed levels'), gr_yn, action=self._parse_setter(RERUNFAILEDLEVELS))
        gr_line = gr_line | np(PList('re schedule on error'), gr_yn, action=self._parse_setter(RESCHEDULEONERROR))
        gr_line = gr_line | np(PList('spool attributes'), gr_yn, action=self._parse_setter(SPOOLATTRIBUTES))
        gr_line = gr_line | np(PList('spool data'), gr_yn, action=self._parse_setter(SPOOLDATA))
        gr_line = gr_line | np(PList('write boot strap'), gr_yn, action=self._parse_setter(WRITEPARTAFTERJOB))

        # }}}
        # {{{ # plain strings

        gr_line = gr_line | np((NOTES,), action=self._parse_setter(NOTES))
        gr_line = gr_line | np((ADDPREFIX, 'add prefix'), action=self._parse_setter(ADDPREFIX))
        gr_line = gr_line | np((ADDSUFFIX, 'add suffix'), action=self._parse_setter(ADDSUFFIX))
        gr_line = gr_line | np((BASE,), action=self._parse_setter(BASE))
        gr_line = gr_line | np((BOOTSTRAP, 'boot strap'), action=self._parse_setter(BOOTSTRAP))
        gr_line = gr_line | np((DIFFERENTIALMAXWAITTIME, 'differential max wait time', 'differentialmaxwait time', 'differentialmax waittime', 'differential maxwaittime', 'differentialmax wait time', 'differential maxwait time', 'differential max waittime'), action=self._parse_setter(DIFFERENTIALMAXWAITTIME))
        gr_line = gr_line | np(('incremental-differentialmaxwaittime','incremental-differential maxwaittime','incremental-differentialmax waittime','incremental-differentialmaxwait time','incremental-differential max waittime','incremental-differential maxwait time','incremental-differentialmax wait time','incremental-differential max wait time',), action=self._parse_setter(IDMAXWAITTIME))
        gr_line = gr_line | np((INCREMENTALMAXRUNTIME, 'incremental max run time', 'incrementalmaxrun time', 'incrementalmax runtime', 'incremental maxruntime', 'incrementalmax run time', 'incremental maxrun time', 'incremental max runtime'), action=self._parse_setter(INCREMENTALMAXRUNTIME))
        gr_line = gr_line | np((MAXFULLINTERVAL, 'max full interval', 'max fullinterval', 'maxfull interval'), action=self._parse_setter(MAXFULLINTERVAL))
        gr_line = gr_line | np((MAXIMUMBANDWIDTH, 'maximum band width', 'maximum bandwidth', 'maximumband width'), action=self._parse_setter(MAXIMUMBANDWIDTH))
        gr_line = gr_line | np((MAXRUNSCHEDTIME, 'max run sched time', 'maxrunsched time', 'maxrun schedtime', 'max runschedtime', 'maxrun sched time', 'max runsched time', 'max run schedtime'), action=self._parse_setter(MAXRUNSCHEDTIME))
        gr_line = gr_line | np((MAXRUNTIME, 'max run time', 'maxrun time', 'max runtime'), action=self._parse_setter(MAXRUNTIME))
        gr_line = gr_line | np((MAXSTARTDELAY, 'max start delay', 'max startdelay', 'maxstart delay'), action=self._parse_setter(MAXSTARTDELAY))
        gr_line = gr_line | np((MAXWAITTIME, 'max wait time', 'max waittime', 'maxwait time'), action=self._parse_setter(MAXWAITTIME))
        gr_line = gr_line | np((REGEXWHERE, 'regex where'), action=self._parse_setter(REGEXWHERE))
        gr_line = gr_line | np((RESCHEDULEINTERVAL, 're schedule interval', 're scheduleinterval', 'reschedule interval'), action=self._parse_setter(RESCHEDULEINTERVAL))
        gr_line = gr_line | np((RUN,), action=self._parse_setter(RUN))
        gr_line = gr_line | np((SPOOLSIZE, 'spool size'), action=self._parse_setter(SPOOLSIZE))
        gr_line = gr_line | np((STRIPPREFIX, 'strip prefix'), action=self._parse_setter(STRIPPREFIX))
        gr_line = gr_line | np((VERIFYJOB, 'verify job'), action=self._parse_setter(VERIFYJOB))
        gr_line = gr_line | np((WHERE,), action=self._parse_setter(WHERE))
        gr_line = gr_line | np((WRITEBOOTSTRAP, 'write boot strap', 'write bootstrap', 'writeboot strap'), action=self._parse_setter(WRITEBOOTSTRAP))

        # }}}
        # The ugliness that is run scripts
        gr_line = gr_line | np(RBJ, gr_stripped_string,
                               action=self._parse_script(runsonclient=0, runswhen='Before'))
        gr_line = gr_line | np(RAJ, gr_stripped_string,
                               action=self._parse_script(runsonclient=0, runswhen='After'))
        gr_line = gr_line | np(RAFJ, gr_stripped_string,
                               action=self._parse_script(runsonsuccess=0, runsonfailure=1,
                                                         runsonclient=0, runswhen='After'))
        gr_line = gr_line | np(CRBJ, gr_stripped_string,
                               action=self._parse_script(runswhen='Before'))
        gr_line = gr_line | np(CRAJ, gr_stripped_string,
                               action=self._parse_script(runswhen='After'))
        
        # This is a complicated one
        gr_script_parts = np(('Command',), gr_stripped_string)
        gr_script_parts = gr_script_parts | np((CONSOLE,), gr_stripped_string)
        gr_script_parts = gr_script_parts | np(PList('Runs When'))
        gr_script_parts = gr_script_parts | np(PList('Runs On Success'), gr_yn)
        gr_script_parts = gr_script_parts | np(PList('Runs On Failure'), gr_yn)
        gr_script_parts = gr_script_parts | np(PList('Runs On Client'), gr_yn)
        gr_script_parts = gr_script_parts | np(PList('Fail Job On Error'), gr_yn)
        gr_script = ((Keyword('Run Script', caseless=True) | Keyword('RunScript', caseless=True)) + nestedExpr('{','}', OneOrMore(gr_script_parts))).setParseAction(self._parse_script_full)
        
        gr_res = OneOrMore(gr_line | gr_script)
        try:
            result = gr_res.parseString(string, parseAll=True)
        except Exception as e:
            print(e)
            raise
        return self.retlabel + ': '+ self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''String representation of a Job, suitable for inclusion in a Director config'''
        self.output = ['%s {' % self.retlabel,'}']
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

# }}}
    # {{{ _fk_reference(fk, string=None): Set/get fk-references

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

# }}}
    # {{{ _load_scripts():

    def _load_scripts(self):
        '''Job scripts are stored separately as Script objects.  This loads them in. '''
        if self[ID]:
            for row in self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s', (self[ID],), asdict=True):
                s = bacula_tools.Script({ID: row[SCRIPT_ID]})
                s.search()
                self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
                self.scripts.append(s)
        return

    # }}}
    # {{{ _parse_script(**kwargs): returns a parser for the script shortcuts

    def _parse_script(self, **kwargs):
        '''Helper function for parsing configuration strings.'''
        def doit(a,b,c):
            s = bacula_tools.Script(kwargs)
            s[COMMAND] = c[2]
            s.search()
            return self._add_script(s)
        return doit

    # }}}
    # {{{ _add_script(s): Add a script to myself

    def _add_script(self, s):
        '''Add a script to the Job.'''
        self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
        self.scripts.append(s)
        row = self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (self[ID], s[ID]))
        if not row:
            self.bc.do_sql('INSERT INTO job_scripts(job_id, script_id) VALUES (%s, %s)', (self[ID], s[ID]))
        return s

    # }}}
    # {{{ _delete_script(s): Remove a script from myself

    def _delete_script(self, s):
        '''Remove a Script from the Job.  This does not actually delete the Script,
        just the linkage to this job.'''
        self.bc.do_sql('DELETE FROM job_scripts WHERE id = %s', (s[ID]))
        self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
        return

    # }}}
    # {{{ _parse_script_full(tokens):

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

# }}}
    # {{{ _cli_special_setup(): setup the weird phrases that go with jobs

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

    # }}}
    # {{{ _cli_special_do_parse(args): handle the weird phrases that go with jobs

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
# }}}
    # {{{ _cli_special_print(): print out the weird phrases that go with jobs

    def _cli_special_print(self):
        '''All of the foreign key objects get printed out here for the CLI.'''
        fmt = '%' + str(self._maxlen) + 's: %s'
        for x in self.REFERENCE_KEYS:
            if self[x] == None: continue
            print(fmt % (x.replace('_id', '').capitalize(), self._fk_reference(x)[NAME]))
        if self.scripts:
            print( '\nScripts')
            for x in self.scripts: print( x)
        return
    # }}}
    # {{{ _cli_special_clone(oid): script links for CLI

    def _cli_special_clone(self, oid):
        '''When cloning, add in script links.'''
        select = 'SELECT %s,script_id FROM job_scripts WHERE job_id = %%s' % self[ID]
        insert = 'INSERT INTO job_scripts (job_id,script_id) VALUES (%s,%s)'
        for row in self.bc.do_sql(select, oid): self.bc.do_sql(insert, row)
        self._load_scripts()
        pass

        # }}}

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
