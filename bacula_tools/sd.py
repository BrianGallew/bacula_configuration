from . import *

# client for interacting with a storage daemon

class SDaemon(BSock):
    '''Client for communicating directly with a storage daemon.
    '''
# {{{ __init__(address, password, myname, port=BACULA_SD_PORT, debug=False, timeout=5):
    def __init__(self, address, password, myname, port=BACULA_SD_PORT, debug=False, timeout=5):
        BSock.__init__(self, address, password, 'Director ' + myname,
                                             port, debug, timeout)
        return
# }}}
# {{{ version(): request version info from the remote daemon (useless?)

    def version(self):
        '''Query the SD for its version.'''
        for line in self.status().split('\n'):
            if 'Version' in line: return line
        return 'Unable to determine version'

    # }}}
# {{{ sd_key(jobid=0, job=None, sdid=0, sdtime=0, authorization='dummy'): SD key setup 

    def sd_key(self, jobid=0, job=None, sdid=0, sdtime=0, authorization='dummy'):
        '''You need an SD key before you can actually do anything with an FD/SD'''
        if not job: job='-Console-.' + self._time()
        self.send('JobId=%(jobid)d Job=%(job)s SDid=%(sdid)d SDtime=%(sdtime)d Authorization=%(authorization)s' % locals())
        return self.recv()

# }}}
