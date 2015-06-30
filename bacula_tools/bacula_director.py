# -*- coding: utf-8 -*-
'''Client for communicating directly with a director. '''
from __future__ import print_function, absolute_import
from . import BSock, ADDRESS, PASSWORD, DIRPORT


class BDirector(BSock):

    '''Client for communicating directly with a director.
    '''

    def __init__(self, director_object, timeout=5):
        BSock.__init__(self, director_object[ADDRESS], director_object[PASSWORD], '*UserAgent*',
                       int(director_object[DIRPORT]), timeout=timeout)
        return
