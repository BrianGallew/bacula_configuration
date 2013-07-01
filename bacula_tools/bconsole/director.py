from base import BSock
# client for interacting with a the Bacula director

class Director(BSock):
    '''Client for communicating directly with a file daemon.
    '''
# {{{ __init__(address, password, port=BACULA_DIR_PORT, debug=False, timeout=5):
    def __init__(self, address, password, port=BACULA_DIR_PORT, debug=False, timeout=5):
        BSock.__init__(self, address, password, '*UserAgent*',
                                             port, debug, timeout)
        return
# }}}
