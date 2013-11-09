from . import *
# client for interacting with a file daemon

class FDaemon(BSock):
    '''Client for communicating directly with a file daemon.
    '''
# {{{ __init__(address, password, myname, port=BACULA_FD_PORT, debug=False, timeout=5):
    def __init__(self, address, password, myname, port=BACULA_FD_PORT, debug=False, timeout=5):
        BSock.__init__(self, address, password, 'Director ' + myname,
                                             port, debug, timeout)
        return
# }}}
# {{{ version(): request version info from the remote daemon (useless?)

    def version(self):
        for line in self.status().split('\n'):
            if 'Version' in line: return line
        return 'Unable to determine version'

    # }}}
