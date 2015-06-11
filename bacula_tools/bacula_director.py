from . import *


class BDirector(BSock):

    '''Client for communicating directly with a director.
    '''

    def __init__(self, director_object, timeout=5):
        BSock.__init__(self, director_object[ADDRESS], director_object[PASSWORD], '*UserAgent*',
                       int(director_object[DIRPORT]), timeout=timeout)
        return
