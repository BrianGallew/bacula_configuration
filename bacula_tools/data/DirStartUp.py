#! /usr/bin/python
# Library to make writing Python tools for Bacula as easy as possible, with lots of code re-use.

# You must import both sys and bacula
import sys, bacula, subprocess
from random import choice
numarray = range(0,100)

# This is the list of Bacula daemon events that you
#  can receive.
class BaculaEvents(object):
    def __init__(self):
        # Called here when a new Bacula Events class is
        #  is created. Normally not used
        noop = 1
        return

    def JobStart(self, job):
        """
        Called here when a new job is started. If you want
        to do anything with the Job, you must register
        events you want to receive.
        """
        noop = 1
        return

  # Bacula Job is going to terminate
    def JobEnd(self, job):
        # If this is a verify job, bail
        if 'Verify' in job.Job: return
        if 'Snap' in job.Job: return # cannot verify snapshot backups

        # Let's truncate any new purged volumes in this pool.
        runcmd = 'purge volume action=Truncate allpools storage=%s\nquit\n' % job.Storage
        # We cannot use job.run() because it won't accept the action
        # keyword for purge.  Le sigh.
        try:
            so = subprocess.Popen('bconsole', shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE).communicate(runcmd)[0]
        except Exception as e:
            job.JobReport = 'Bailing ... '
            job.JobReport = str(e)
            return
        job.JobReport = "ran volume purge command: %s" % so

        # This bit gives us a chance (5%) of running a verify job against this one.
        if choice(numarray) < 5:          # 5% chance of running a verify
            runcmd = 'run job=%s-Verify jobid=%d yes' % (job.Job, job.JobId)
            newjob = job.run(runcmd)
            job.JobReport="%s: jobid=%d\n" % (runcmd, newjob)
        return

  # Called here when the Bacula daemon is going to exit
    def Exit(self, job):
        noop = 1
        return

# This is what makes it actually work
bacula.set_events(BaculaEvents()) # register daemon events desired
