#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (ADDRESS, CLIENT_ID, DIRADDRESSES, DIRECTORS,
                          DIRPORT, DbDict, FD_CONNECT_TIMEOUT,
                          HEARTBEATINTERVAL, MAXIMUMCONCURRENTJOBS,
                          MAXIMUMCONSOLECONNECTIONS, MESSAGES, MESSAGES_ID,
                          NAME, PASSWORD, PIDDIRECTORY, QUERYFILE,
                          SCRIPTS_DIRECTORY, SD_CONNECT_TIMEOUT,
                          SOURCEADDRESS, STATISTICS_RETENTION,
                          WORKINGDIRECTORY, STORAGE_ID)
import bacula_tools
import logging
import optparse


class Director(DbDict):
    SETUP_KEYS = [ADDRESS, FD_CONNECT_TIMEOUT, HEARTBEATINTERVAL, PASSWORD,
                  PIDDIRECTORY, QUERYFILE, SCRIPTS_DIRECTORY,
                  SD_CONNECT_TIMEOUT, SOURCEADDRESS, STATISTICS_RETENTION,
                  WORKINGDIRECTORY]
    INT_KEYS = [(DIRPORT, 9101), MAXIMUMCONCURRENTJOBS,
                MAXIMUMCONSOLECONNECTIONS, ]
    NULL_KEYS = [MESSAGES_ID, DIRADDRESSES]
    table = DIRECTORS
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 1

    def __str__(self):
        '''String representation of a Director, suitable for inclusion in director.conf'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        for key in self.SETUP_KEYS + self.INT_KEYS:
            if key == ADDRESS and self[ADDRESS]:
                self.output.insert(-1, '  DirAddress = %s' % self[key])
            elif key == SOURCEADDRESS and self[SOURCEADDRESS]:
                self.output.insert(-1, '  DirSourceAddress = %s' % self[key])
            else:
                self._simple_phrase(key)
        # set the messages
        m = self._fk_reference(MESSAGES_ID)
        self.output.insert(-1, '  %s = "%s"' %
                           (MESSAGES.capitalize(), m[NAME]))
        if self[DIRADDRESSES]:
            self.output.insert(-1, '  %s = {' % DIRADDRESSES.capitalize())
            self.output.insert(-1,  self[DIRADDRESSES])
            self.output.insert(-1, '  }')
        return '\n'.join(self.output)

    def fd(self):
        '''This is what we'll call to dump out the config for the file daemon'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        if getattr(self, CLIENT_ID, None):
            a = bacula_tools.PasswordStore(
                bacula_tools.Client().search(self.client_id), self)
            if getattr(a, PASSWORD, None):
                self.output.insert(-1, '  Password = "%s"' % a.password)
        return '\n'.join(self.output)

    def sd(self):
        '''This is what we'll call to dump out the config for the storage daemon'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        if getattr(self, STORAGE_ID, None):
            a = bacula_tools.PasswordStore(
                bacula_tools.Storage().search(self.storage_id), self)
            if getattr(a, PASSWORD, None):
                self.output.insert(-1, '  Password = "%s"' % a.password)
        return '\n'.join(self.output)

    def bconsole(self):
        '''This is what we'll call to dump out the config for the bconsole'''
        self.output = ['Director {\n  Name = "%(name)s"' % self, '}']
        if self[DIRPORT]:
            self._simple_phrase(DIRPORT)
            self._simple_phrase(ADDRESS)
        else:
            # This has the more silly way of doing stuff.  bleah.
            self.output.insert(-1,
                               '  Dir Addresses = {\n  %s  \n  }\n' % self[DIRADDRESSES])
        self._simple_phrase(PASSWORD)
        return '\n'.join(self.output)

    def _cli_special_setup(self):
        '''Handle setting by the CLI of the Message to be used by this %s.''' % self.word.capitalize()
        group = optparse.OptionGroup(self.parser,
                                     "Object Setters",
                                     "Various objects associated with a %s" % self.word.capitalize())
        group.add_option('--message-set')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''Enable the CLI to set the Message to be used by this Director.'''
        if args.message_set == None:
            return
        if args.message_set == '':
            return self.set(MESSAGES_ID, None)
        target = Messages().search(args.message_set)
        if target[ID]:
            self.set(MESSAGES_ID, target[ID])
        else:
            print('Unable to find a match for %s, continuing' %
                  args.message_set)
        return

    def _cli_special_print(self):
        '''Print out the Message for this Director'''
        if not self[MESSAGES_ID]:
            return
        fmt = '%' + str(self._maxlen) + 's: %s'
        print(fmt % ('Messages', self._fk_reference(MESSAGES_ID)[NAME]))
        return


def main():
    s = Director()
    s.cli()

if __name__ == "__main__":
    main()
