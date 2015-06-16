# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (BSock, BACULA_FD_PORT)


class FDaemon(BSock):

    '''Client for communicating directly with a file daemon.
    '''

    def __init__(self, address, password, myname, port=BACULA_FD_PORT, timeout=5):
        BSock.__init__(
            self, address, password, 'Director ' + myname, port, timeout)
        return

    def version(self):
        for line in self.status().split('\n'):
            if 'Version' in line:
                return line
        return 'Unable to determine version'
