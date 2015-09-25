#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (ALERTCOMMAND, ALWAYSOPEN, ARCHIVEDEVICE,
                          AUTOCHANGER, AUTOMATICMOUNT, AUTOSELECT,
                          BACKWARDSPACEFILE, BACKWARDSPACERECORD,
                          BLOCKCHECKSUM, BLOCKPOSITIONING, BSFATEOM,
                          CHANGERCOMMAND, CHANGERDEVICE,
                          CLIENTCONNECTWAIT, CLOSEONPOLL, DEVICE,
                          DEVICETYPE, DRIVEINDEX, DbDict,
                          FASTFORWARDSPACEFILE, FORWARDSPACEFILE,
                          FORWARDSPACERECORD, HARDWAREENDOFMEDIUM, ID,
                          LABELMEDIA, MAXIMUMBLOCKSIZE,
                          MAXIMUMCHANGERWAIT, MAXIMUMCONCURRENTJOBS,
                          MAXIMUMFILESIZE, MAXIMUMJOBSPOOLSIZE,
                          MAXIMUMNETWORKBUFFERSIZE, MAXIMUMOPENWAIT,
                          MAXIMUMPARTSIZE, MAXIMUMREWINDWAIT,
                          MAXIMUMSPOOLSIZE, MAXIMUMVOLUMESIZE, MEDIATYPE,
                          MINIMUMBLOCKSIZE, MOUNTCOMMAND, MOUNTPOINT, NAME,
                          OFFLINEONUNMOUNT, RANDOMACCESS, REMOVABLEMEDIA,
                          SPOOLDIRECTORY, TWOEOF, UNMOUNTCOMMAND,
                          USEMTIOCGET, VOLUMEPOLLINTERVAL, )
import bacula_tools
import logging
import optparse


class Device(DbDict):
    SETUP_KEYS = [ARCHIVEDEVICE, DEVICETYPE, MEDIATYPE, CHANGERDEVICE,
                  CHANGERCOMMAND, ALERTCOMMAND, DRIVEINDEX, MAXIMUMCONCURRENTJOBS,
                  MAXIMUMCHANGERWAIT, MAXIMUMREWINDWAIT, MAXIMUMOPENWAIT,
                  VOLUMEPOLLINTERVAL, MOUNTPOINT, MOUNTCOMMAND, UNMOUNTCOMMAND,
                  MINIMUMBLOCKSIZE, MAXIMUMBLOCKSIZE, MAXIMUMVOLUMESIZE,
                  MAXIMUMFILESIZE, MAXIMUMNETWORKBUFFERSIZE, MAXIMUMSPOOLSIZE,
                  MAXIMUMJOBSPOOLSIZE, SPOOLDIRECTORY, MAXIMUMPARTSIZE,
                  CLIENTCONNECTWAIT, ]
    BOOL_KEYS = [AUTOSELECT, REMOVABLEMEDIA, BLOCKCHECKSUM,
                 HARDWAREENDOFMEDIUM, FASTFORWARDSPACEFILE, USEMTIOCGET,
                 AUTOMATICMOUNT, BACKWARDSPACERECORD, BACKWARDSPACEFILE,
                 FORWARDSPACERECORD, FORWARDSPACEFILE, BLOCKPOSITIONING,
                 AUTOCHANGER, ALWAYSOPEN, CLOSEONPOLL, RANDOMACCESS, BSFATEOM,
                 TWOEOF, OFFLINEONUNMOUNT, LABELMEDIA, ]
    table = DEVICE
    _insert = 'INSERT INTO device_link (device_id, storage_id) values (%s, %s)'
    _delete = 'DELETE FROM device_link where device_id = %s and storage_id = %s'
    _select = 'SELECT storage_id FROM device_link where device_id = %s'

    def __str__(self):
        '''String representation of a Device suitable for inclusion in a
        configuration file.

        '''
        self.output = ['Device {\n  Name = "%(name)s"' % self, '}']

        for key in self.SETUP_KEYS:
            self._simple_phrase(key)
        for key in self.BOOL_KEYS:
            self._yesno_phrase(key)

        return '\n'.join(self.output)

    def link(self, obj):
        '''Devices belong to Storage Daemons, but there's no intrinsic way to know
        that a device belongs to a daemon, so we have a table that provides
        links between the two.  This member, given a Storage object, will
        link the Device to the Storage.
        '''
        try:
            self.bc.do_sql(self._insert, (self[ID], obj[ID]))
        except Exception as e:
            if e.args[0] == 1062:
                # 1062 is what happens when you try to insert a duplicate row
                pass
            else:
                print(e)
                raise

    def unlink(self, obj):
        '''Remove the linkage between a Device and a Storage'''
        self.bc.do_sql(self._delete, (self[ID], obj[ID]))
        return

    def find_linked(self):
        '''Find all the linked Storage servers'''
        result = []
        for row in self.bc.do_sql(self._select, self[ID]):
            result.append(bacula_tools.Storage().search(row[0]))
        return result

    def _cli_special_setup(self):
        '''Enable the CLI to (un)link devices to/from Sotrage Daemons.'''
        group = optparse.OptionGroup(self.parser, "Storage daemon links",
                                     "A device is associated with one or more storage daemons.")
        group.add_option('--add-link', metavar='STORAGE_DAEMON')
        group.add_option('--remove-link', metavar='STORAGE_DAEMON')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''Handle any attempts by the CLI to (un)link the Device to/from Storage'''
        if args.add_link:
            s = bacula_tools.Storage().search(args.add_link)
            if not s[ID]:
                s.search(args.add_link)
            if not s[ID]:
                print(
                    '\n***WARNING***: Unable to find a Storage Daemon identified by "%s".  Not linked.\n' % args.add_link)
                return
            self.link(s)

        if args.remove_link:
            s = bacula_tools.Storage().search(args.remove_link)
            if not s[ID]:
                s.search(args.remove_link)
            if not s[ID]:
                print(
                    '\n***WARNING***: Unable to find a Storage Daemon identified by "%s".  Not unlinked.\n' % args.remove_link)
                return
            self.unlink(s)

        return

    def _cli_special_print(self):
        '''Print any linked Storage'''
        for s in self.find_linked():
            print(('%' + str(self._maxlen) + 's: %s') %
                  ('Storage Daemon', s[NAME]))
        return

    def _cli_special_clone(self, oid):
        '''Any clones of this device will be linked to the same Storage.'''
        for row in self.bc.do_sql(self._select, oid):
            self.bc.do_sql(self._insert, (self[ID], row[0]))
        return

        # }}}


def main():
    s = Device()
    s.cli()

if __name__ == "__main__":
    main()
