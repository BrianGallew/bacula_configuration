from __future__ import print_function
from bacula_tools import *
from bacula_tools.scripts import Script
import bacula_tools

RBJ = PList('Run Before Job')
RAJ = PList('Run After Job')
RAFJ = PList( 'Run After Failed Job')
CRBJ = PList('Client Run Before Job')
CRAJ = PList('Client Run After Job')

class Job(DbDict):
    NULL_KEYS = [
        # Enum
        TYPE, LEVEL,
        # Strings
        NOTES, ADDPREFIX, ADDSUFFIX, BASE, BOOTSTRAP, DIFFERENTIALMAXWAITTIME, IDMAXWAITTIME,
        INCREMENTALMAXRUNTIME, MAXFULLINTERVAL, MAXIMUMBANDWIDTH, MAXRUNSCHEDTIME, MAXRUNTIME,
        MAXSTARTDELAY, MAXWAITTIME, REGEXWHERE, RESCHEDULEINTERVAL, RUN, SPOOLSIZE, 
        STRIPPREFIX, VERIFYJOB, WHERE, WRITEBOOTSTRAP,
        # keys with values
        (REPLACE, 'always'), (NAME, ''),
        ]
    REFERENCE_KEYS = [          # foreign keys
        DIFFERENTIALPOOL_ID, FILESET_ID, FULLPOOL_ID, CLIENT_ID,
        INCREMENTALPOOL_ID, MESSAGES_ID, POOL_ID, SCHEDULE_ID, STORAGE_ID,
        ]        
    INT_KEYS = [MAXIMUMCONCURRENTJOBS, RESCHEDULETIMES, PRIORITY]
    TRUE_KEYS = [ENABLED, PREFERMOUNTEDVOLUMES]
    FALSE_KEYS = [
        ACCURATE, ALLOWDUPLICATEJOBS, ALLOWMIXEDPRIORITY, CANCELLOWERLEVELDUPLICATES,
        CANCELQUEUEDDUPLICATES, CANCELRUNNINGDUPLICATES, (JOBDEF, 0), 
        PREFIXLINKS, PRUNEFILES, PRUNEJOBS, PRUNEVOLUMES, RERUNFAILEDLEVELS, RESCHEDULEONERROR,
        SPOOLATTRIBUTES, SPOOLDATA, WRITEPARTAFTERJOB
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

        gr_line = gr_line | np(('differential pool', 'differentialpool'), action=self._parse_setter(DIFFERENTIALPOOL_ID))
        gr_line = gr_line | np((FILESET, 'file set'), action=self._parse_setter(FILESET_ID, dereference=True))
        gr_line = gr_line | np(('full pool', 'fullpool'), action=self._parse_setter(FULLPOOL_ID))
        gr_line = gr_line | np((CLIENT,), action=self._parse_setter(CLIENT_ID, dereference=True))
        gr_line = gr_line | np(('incremental pool', 'incrementalpool'), action=self._parse_setter(INCREMENTALPOOL_ID))
        gr_line = gr_line | np((MESSAGES,), action=self._parse_setter(MESSAGES_ID, dereference=True))
        gr_line = gr_line | np((POOL,), action=self._parse_setter(POOL_ID, dereference=True))
        gr_line = gr_line | np((SCHEDULE,), action=self._parse_setter(SCHEDULE_ID, dereference=True))
        gr_line = gr_line | np((STORAGE,), action=self._parse_setter(STORAGE_ID, dereference=True))
        gr_line = gr_line | np(('job defs', 'jobdefs'), action=self._parse_setter(JOB_ID, dereference=True))

        # }}}
        # {{{ # INTs

        gr_line = gr_line | np((MAXIMUMCONCURRENTJOBS, 'maximum concurrent jobs', 'maximum concurrentjobs', 'maximumconcurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
        gr_line = gr_line | np((RESCHEDULETIMES, 'rescheduletimes', 'reschedule times'), gr_number, action=self._parse_setter(RESCHEDULETIMES))
        gr_line = gr_line | np((PRIORITY,), gr_number, action=self._parse_setter(PRIORITY))

        # }}}
        # {{{ # True/False

        gr_line = gr_line | np((ACCURATE,), gr_yn, action=self._parse_setter(ACCURATE))
        gr_line = gr_line | np((ALLOWDUPLICATEJOBS, 'allow duplicate jobs', 'allow duplicatejobs', 'allowduplicate jobs'), gr_yn, action=self._parse_setter(ALLOWDUPLICATEJOBS))
        gr_line = gr_line | np((ALLOWMIXEDPRIORITY, 'allow mixed priority', 'allow mixedpriority', 'allowmixed priority'), gr_yn, action=self._parse_setter(ALLOWMIXEDPRIORITY))
        gr_line = gr_line | np((CANCELLOWERLEVELDUPLICATES, 'cancel lower level duplicates', 'cancellowerlevel duplicates', 'cancellower levelduplicates', 'cancel lowerlevelduplicates', 'cancellower level duplicates', 'cancel lowerlevel duplicates', 'cancel lower levelduplicates'), gr_yn, action=self._parse_setter(CANCELLOWERLEVELDUPLICATES))
        gr_line = gr_line | np((CANCELQUEUEDDUPLICATES, 'cancel queued duplicates', 'cancel queuedduplicates', 'cancelqueued duplicates'), gr_yn, action=self._parse_setter(CANCELQUEUEDDUPLICATES))
        gr_line = gr_line | np((CANCELRUNNINGDUPLICATES, 'cancel running duplicates', 'cancel runningduplicates', 'cancelrunning duplicates'), gr_yn, action=self._parse_setter(CANCELRUNNINGDUPLICATES))
        gr_line = gr_line | np((ENABLED,), gr_yn, action=self._parse_setter(ENABLED))
        gr_line = gr_line | np((PREFERMOUNTEDVOLUMES, 'prefer mounted volumes', 'prefer mountedvolumes', 'prefermounted volumes'), gr_yn, action=self._parse_setter(PREFERMOUNTEDVOLUMES))
        gr_line = gr_line | np((PREFIXLINKS, 'prefix links'), gr_yn, action=self._parse_setter(PREFIXLINKS))
        gr_line = gr_line | np((PRUNEFILES, 'prune files'), gr_yn, action=self._parse_setter(PRUNEFILES))
        gr_line = gr_line | np((PRUNEJOBS, 'prune jobs'), gr_yn, action=self._parse_setter(PRUNEJOBS))
        gr_line = gr_line | np((PRUNEVOLUMES, 'prune volumes'), gr_yn, action=self._parse_setter(PRUNEVOLUMES))
        gr_line = gr_line | np((RERUNFAILEDLEVELS, 're run failed levels', 're runfailedlevels', 'rerun failedlevels', 'rerunfailed levels', 'rerun failed levels', 're runfailed levels', 're run failedlevels'), gr_yn, action=self._parse_setter(RERUNFAILEDLEVELS))
        gr_line = gr_line | np((RESCHEDULEONERROR, 're schedule on error', 'rescheduleon error', 'reschedule onerror', 're scheduleonerror', 'reschedule on error', 're scheduleon error', 're schedule onerror'), gr_yn, action=self._parse_setter(RESCHEDULEONERROR))
        gr_line = gr_line | np((SPOOLATTRIBUTES, 'spool attributes'), gr_yn, action=self._parse_setter(SPOOLATTRIBUTES))
        gr_line = gr_line | np((SPOOLDATA, 'spool data'), gr_yn, action=self._parse_setter(SPOOLDATA))
        gr_line = gr_line | np((WRITEBOOTSTRAP, 'write boot strap', 'writeboot strap', 'write bootstrap'), gr_yn, action=self._parse_setter(WRITEPARTAFTERJOB))

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
        result = gr_res.parseString(string, parseAll=True)
        return self.retlabel + ': '+ self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['%s {\n  Name = "%s"' % (self.retlabel, self[NAME]),'}']
        for x in self.NULL_KEYS: self._simple_phrase(x)
        for x in self.INT_KEYS: self._simple_phrase(x)
        for x in self.REFERENCE_KEYS:
            if self[x] == None: continue
            self.output.insert(-1,'  %s = "%s"' % (x.replace('_id', '').capitalize(), self._fk_reference(x)[NAME]))
        if self[JOB_ID]: self.output.insert(-1,'  JobDefs = "%s"' % self._fk_reference(JOB_ID)[NAME])

        for x in self.FALSE_KEYS: self._yesno_phrase(x, onlytrue=True)
        for x in self.TRUE_KEYS: self._yesno_phrase(x, onlyfalse=True)
        for x in self.scripts: self.output.insert(-1, str(x))
        return '\n'.join(self.output)

# }}}
    # {{{ _fk_reference(fk, string=None): Set/get fk-references

    def _fk_reference(self, fk, string=None):
        key = fk.replace('_id', '')
        if 'pool' in key: key = 'pool'
        obj = bacula_tools._DISPATCHER[key]()
        if string:
            obj.search(string.strip())
            if not obj[ID]: obj._set_name(string.strip())
            if not self[fk] == obj[ID]: self._set(fk, obj[ID])
        else: obj.search(None, id=self[fk])
        return obj

# }}}
    # {{{ _load_scripts():

    def _load_scripts(self):
        if self[ID]:
            for row in self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s', (self[ID],), asdict=True):
                s = Script({ID: row[SCRIPT_ID]})
                s.search()
                self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
                self.scripts.append(s)
        return

    # }}}
    # {{{ _parse_script(**kwargs): returns a parser for the script shortcuts

    def _parse_script(self, **kwargs):
        def doit(a,b,c):
            from bacula_tools.scripts import Script
            s = Script(kwargs)
            s[COMMAND] = c[2]
            s.search()
            return self._add_script(s)
        return doit

    # }}}
    # {{{ _add_script(s): Add a script to myself

    def _add_script(self, s):
        self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
        self.scripts.append(s)
        row = self.bc.do_sql('SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (self[ID], s[ID]))
        if not row:
            self.bc.do_sql('INSERT INTO job_scripts(job_id, script_id) VALUES (%s, %s)', (self[ID], s[ID]))
        return s

    # }}}
    # {{{ _delete_script(s): Remove a script from myself

    def _delete_script(self, s):
        self.bc.do_sql('DELETE FROM job_scripts WHERE id = %s', (s[ID]))
        self.scripts = [x for x in self.scripts if not x[ID] == s[ID]]
        return

    # }}}
    # {{{ _parse_script_full(tokens):

    def _parse_script_full(self, tokens):
        s = Script()
        values = tokens[1]
        while values:
            k,n,v = values[:3]
            del values[:3]
            s[k.lower()] = v
        self._add_script(s.search())
        return

# }}}

class JobDef(Job):
    SETUP_KEYS = [(REPLACE, 'always'), (NAME, ''), (JOBDEF, 1)]
    retlabel = 'JobDef'
    
