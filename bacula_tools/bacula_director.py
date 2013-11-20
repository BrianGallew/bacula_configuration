from . import *
# client for interacting with a the Bacula director

class BDirector(BSock):
    '''Client for communicating directly with a director.
    '''
# {{{ __init__(director_object, timeout=5):
    def __init__(self, director_object, debug=False, timeout=5):
        BSock.__init__(self, director_object[ADDRESS], director_object[PASSWORD], '*UserAgent*',
                       int(director_object[DIRPORT]), timeout)
        return
# }}}
