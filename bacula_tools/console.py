#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (ADDRESS, CATALOGACL, CLIENTACL, CLIENT_ID,
                          COMMANDACL, CONSOLES, DIRECTOR_ID, DIRPORT,
                          DbDict, FILESETACL, JOBACL, POOLACL, SCHEDULEACL,
                          STORAGEACL, WHEREACL, )
import bacula_tools
import logging


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
                  POOLACL, SCHEDULEACL, STORAGEACL, WHEREACL, DIRPORT, ADDRESS]
    table = CONSOLES
    IDTAG = 4

    def __str__(self):
        self.output = ['Console {\n  Name = "%(name)s"' % self, '}']

        for key in self.SETUP_KEYS:
            if key in [DIRPORT, ADDRESS]:
                continue
            self._simple_phrase(key)
        if getattr(self, DIRECTOR_ID, None):
            c = bacula_tools.Director().search(self.director_id)
            a = PasswordStore(c, self)
            self.output.insert(-1, '  Password = "%s"' % a.password)
        return '\n'.join(self.output)

    def fd(self):
        self.output = [
            'Director {\n  Name = "%(name)s"' % self, '  Monitor = yes', '}']
        if getattr(self, CLIENT_ID, None):
            c = bacula_tools.Client().search(self.client_id)
            a = PasswordStore(c, self)
            self.output.insert(-1, '  Password = "%s"' % a.password)
        return '\n'.join(self.output)

    def bconsole(self):
        '''This is what we'll call to dump out the config for the bconsole'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        self._simple_phrase(DIRPORT)
        self._simple_phrase(ADDRESS)
        if getattr(self, DIRECTOR_ID, None):
            c = bacula_tools.Director().search(self.director_id)
            a = PasswordStore(c, self)
            self.output.insert(-1, '  Password = "%s"' % a.password)
        return '\n'.join(self.output)


def main():  # Implement the CLI for managing Consoles
    s = Console()
    s.cli()

if __name__ == "__main__":
    main()
