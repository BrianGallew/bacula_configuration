from bacula_tools import (BACULA_SD_PORT, BSock)


class SDaemon(BSock):

    '''Client for communicating directly with a storage daemon.
    '''

    def __init__(self, address, password, myname, port=BACULA_SD_PORT, timeout=5):
        BSock.__init__(self, address, password, 'SD: Bacula Director ' + myname,
                       port, timeout)
        return

    def version(self):
        '''Query the SD for its version.'''
        for line in self.status().split('\n'):
            if 'Version' in line:
                return line
        return 'Unable to determine version'

    def sd_key(self, jobid=0, job=None, sdid=0, sdtime=0, authorization='dummy'):
        '''You need an SD key before you can actually do anything with an FD/SD'''
        if not job:
            job = '-Console-.' + self._time()
        self.send(
            'JobId=%(jobid)d Job=%(job)s SDid=%(sdid)d SDtime=%(sdtime)d Authorization=%(authorization)s' % locals())
        return self.recv()
