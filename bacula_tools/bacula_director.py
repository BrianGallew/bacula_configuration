from . import *
# client for interacting with a the Bacula director

class BDirector(BSock):
    '''Client for communicating directly with a director.
    '''
    def __init__(self, director_object, debug=False, timeout=5):
        BSock.__init__(self, director_object[ADDRESS], director_object[PASSWORD], '*UserAgent*',
                       int(director_object[DIRPORT]), debug=debug, timeout=timeout)
        return
