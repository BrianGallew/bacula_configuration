#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (ADDRESS, CATALOGACL, CLIENTACL, CLIENT_ID,
                          COMMANDACL, CONSOLES, DIRECTOR_ID, DIRPORT,
                          DbDict, FILESETACL, JOBACL, POOLACL, SCHEDULEACL,
                          STORAGEACL, WHEREACL, PASSWORD)
import bacula_tools
import logging
logger = logging.getLogger(__name__)


class Console(DbDict):

    '''This is for configuring bconsole access.  Unfortunately, there's no good
    way to extract this for constructing a bconsole.conf.  You can set up
    conventions that a client hostname should match the name of the Console,
    but that isn't going to be very satisfactory.

    TODO: this needs to be re-architected, along with the Director class.
    The Console shows up as a "Director" resource in the FD/SD, which is
    really quite stupid.

    '''
    SETUP_KEYS = [CATALOGACL, CLIENTACL, COMMANDACL, FILESETACL, JOBACL,
                  POOLACL, SCHEDULEACL, STORAGEACL, WHEREACL]
    NULL_KEYS = [DIRECTOR_ID, ]
    table = CONSOLES
    IDTAG = 4

    def __str__(self):
        self.output = ['Console {\n  Name = "%(name)s"' % self, '}']

        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        c = bacula_tools.Director().search(self[DIRECTOR_ID])
        self.output.insert(-1, '  Password = "%s"' % c[PASSWORD])
        return '\n'.join(self.output)

    def fd(self):
        self.output = [
            'Director {\n  Name = "%(name)s"' % self, '  Monitor = yes', '}']
        if getattr(self, CLIENT_ID, None):
            c = bacula_tools.Client().search(self.client_id)
            a = bacula_tools.PasswordStore(c, self)
            self.output.insert(-1, '  Password = "%s"' % a.password)
        return '\n'.join(self.output)

    def bconsole(self):
        '''This is what we'll call to dump out the config for the bconsole'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        c = bacula_tools.Director().search(self[DIRECTOR_ID])
        self.output.insert(-1, '  Password = "%s"' % c[PASSWORD])
        if ADDRESS in c:
            self.output.insert(-1,
                               '  DirPort = %(dirport)s\n  Address = %(address)s' % c)
        else:
            self.output.insert(-1,
                               '  Dir Addresses = {\n  %s  \n  }\n' % c[DIRADDRESSES])
        return '\n'.join(self.output)


def main():  # Implement the CLI for managing Consoles
    s = Console()
    s.cli()

if __name__ == "__main__":
    main()
