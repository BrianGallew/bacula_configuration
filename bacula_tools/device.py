#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Device(DbDict):
    SETUP_KEYS = [
        ARCHIVEDEVICE, DEVICETYPE, MEDIATYPE, CHANGERDEVICE, CHANGERCOMMAND, ALERTCOMMAND,
        DRIVEINDEX, MAXIMUMCONCURRENTJOBS, MAXIMUMCHANGERWAIT, MAXIMUMREWINDWAIT,
        MAXIMUMOPENWAIT, VOLUMEPOLLINTERVAL, MOUNTPOINT, MOUNTCOMMAND, UNMOUNTCOMMAND,
        MINIMUMBLOCKSIZE, MAXIMUMBLOCKSIZE, MAXIMUMVOLUMESIZE, MAXIMUMFILESIZE,
        MAXIMUMNETWORKBUFFERSIZE, MAXIMUMSPOOLSIZE, MAXIMUMJOBSPOOLSIZE, SPOOLDIRECTORY,
        MAXIMUMPARTSIZE, CLIENTCONNECTWAIT,
        ]
    BOOL_KEYS = [
        AUTOSELECT, REMOVABLEMEDIA, BLOCKCHECKSUM, HARDWAREENDOFMEDIUM,
        FASTFORWARDSPACEFILE, USEMTIOCGET, AUTOMATICMOUNT,
        BACKWARDSPACERECORD, BACKWARDSPACEFILE, FORWARDSPACERECORD,
        FORWARDSPACEFILE, BLOCKPOSITIONING, AUTOCHANGER, ALWAYSOPEN, CLOSEONPOLL,
        RANDOMACCESS, BSFATEOM, TWOEOF, OFFLINEONUNMOUNT, LABELMEDIA,
        ]
    table = DEVICE
    _insert = 'INSERT INTO device_link (device_id, storage_id) values (%s, %s)'
    _delete = 'DELETE FROM device_link where device_id = %s and storage_id = %s'
    _select = 'SELECT storage_id FROM device_link where device_id = %s'
    # {{{ parse_string(string, obj=None): Entry point for a recursive descent parser

    def parse_string(self, string, obj=None):
        # {{{ boilerplate.  Sigh

        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith, nums
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        # }}}

        gr_line =           np(PList(NAME), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np(PList('alert command'), action=self._parse_setter(ALERTCOMMAND))
        gr_line = gr_line | np(PList('archive device'), action=self._parse_setter(ARCHIVEDEVICE))
        gr_line = gr_line | np(PList('changer command'), action=self._parse_setter(CHANGERCOMMAND))
        gr_line = gr_line | np(PList('changer device'), action=self._parse_setter(CHANGERDEVICE))
        gr_line = gr_line | np(PList('client connect wait'), action=self._parse_setter(CLIENTCONNECTWAIT))
        gr_line = gr_line | np(PList('device type'), action=self._parse_setter(DEVICETYPE))
        gr_line = gr_line | np(PList('drive index'), gr_number, action=self._parse_setter(DRIVEINDEX, c_int=True))
        gr_line = gr_line | np(PList('maximum block size'), action=self._parse_setter(MAXIMUMBLOCKSIZE))
        gr_line = gr_line | np(PList('maximum changer wait'), action=self._parse_setter(MAXIMUMCHANGERWAIT))
        gr_line = gr_line | np(PList('maximum concurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS, c_int=True))
        gr_line = gr_line | np(PList('maximum file size'), action=self._parse_setter(MAXIMUMFILESIZE))
        gr_line = gr_line | np(PList('maximum job spool size'), action=self._parse_setter(MAXIMUMJOBSPOOLSIZE))
        gr_line = gr_line | np(PList('maximum network buffer size'), action=self._parse_setter(MAXIMUMNETWORKBUFFERSIZE))
        gr_line = gr_line | np(PList('maximum open wait'), action=self._parse_setter(MAXIMUMOPENWAIT))
        gr_line = gr_line | np(PList('maximum part size'), action=self._parse_setter(MAXIMUMPARTSIZE))
        gr_line = gr_line | np(PList('maximum rewind wait'), action=self._parse_setter(MAXIMUMREWINDWAIT))
        gr_line = gr_line | np(PList('maximum spool size'), action=self._parse_setter(MAXIMUMSPOOLSIZE))
        gr_line = gr_line | np(PList('maximum volume size'), action=self._parse_setter(MAXIMUMVOLUMESIZE))
        gr_line = gr_line | np(PList('media type'), action=self._parse_setter(MEDIATYPE))
        gr_line = gr_line | np(PList('minimum block size'), action=self._parse_setter(MINIMUMBLOCKSIZE))
        gr_line = gr_line | np(PList('mount command'), action=self._parse_setter(MOUNTCOMMAND))
        gr_line = gr_line | np(PList('mount point'), action=self._parse_setter(MOUNTPOINT))
        gr_line = gr_line | np(PList('spool directory'), action=self._parse_setter(SPOOLDIRECTORY))
        gr_line = gr_line | np(PList('unmount command'), action=self._parse_setter(UNMOUNTCOMMAND))
        gr_line = gr_line | np(PList('volume poll interval'), action=self._parse_setter(VOLUMEPOLLINTERVAL))

        gr_line = gr_line | np(PList('always open'), gr_yn, action=self._parse_setter(ALWAYSOPEN))
        gr_line = gr_line | np(PList('auto changer'), gr_yn, action=self._parse_setter(AUTOCHANGER))
        gr_line = gr_line | np(PList('auto select'), gr_yn, action=self._parse_setter(AUTOSELECT))
        gr_line = gr_line | np(PList('automatic mount'), gr_yn, action=self._parse_setter(AUTOMATICMOUNT))
        gr_line = gr_line | np(PList('backward space file'), gr_yn, action=self._parse_setter(BACKWARDSPACEFILE))
        gr_line = gr_line | np(PList('backward space record'), gr_yn, action=self._parse_setter(BACKWARDSPACERECORD))
        gr_line = gr_line | np(PList('block check sum'), gr_yn, action=self._parse_setter(BLOCKCHECKSUM))
        gr_line = gr_line | np(PList('block positioning'), gr_yn, action=self._parse_setter(BLOCKPOSITIONING))
        gr_line = gr_line | np(PList('bsf at eom'), gr_yn, action=self._parse_setter(BSFATEOM))
        gr_line = gr_line | np(PList('close on poll'), gr_yn, action=self._parse_setter(CLOSEONPOLL))
        gr_line = gr_line | np(PList('fast forward space file'), gr_yn, action=self._parse_setter(FASTFORWARDSPACEFILE))
        gr_line = gr_line | np(PList('forward space file'), gr_yn, action=self._parse_setter(FORWARDSPACEFILE))
        gr_line = gr_line | np(PList('forward space record'), gr_yn, action=self._parse_setter(FORWARDSPACERECORD))
        gr_line = gr_line | np(PList('hardware end of medium'), gr_yn, action=self._parse_setter(HARDWAREENDOFMEDIUM))
        gr_line = gr_line | np(PList('label media'), gr_yn, action=self._parse_setter(LABELMEDIA))
        gr_line = gr_line | np(PList('offline on unmount'), gr_yn, action=self._parse_setter(OFFLINEONUNMOUNT))
        gr_line = gr_line | np(PList('random access'), gr_yn, action=self._parse_setter(RANDOMACCESS))
        gr_line = gr_line | np(PList('removable media'), gr_yn, action=self._parse_setter(REMOVABLEMEDIA))
        gr_line = gr_line | np(PList('two eof'), gr_yn, action=self._parse_setter(TWOEOF))
        gr_line = gr_line | np(PList('use mtiocget'), gr_yn, action=self._parse_setter(USEMTIOCGET))

        gr_res = OneOrMore(gr_line)

        result = gr_res.parseString(string, parseAll=True)
        if obj: self.link(obj)
        return 'Device: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''String representation of a Device suitable for inclusion in a
        configuration file.

        '''
        self.output = ['Device {\n  Name = "%(name)s"' % self,'}']
        
        for key in self.SETUP_KEYS: self._simple_phrase(key)
        for key in self.BOOL_KEYS: self._yesno_phrase(key)

        return '\n'.join(self.output)

# }}}
    # {{{ link(obj): link the device to a storage daemon

    def link(self, obj):
        '''Devices belong to Storage Daemons, but there's no intrinsic way to know
        that a device belongs to a daemon, so we have a table that provides
        links between the two.  This member, given a Storage object, will
        link the Device to the Storage.
        '''
        try:
            self.bc.do_sql(self._insert, (self[ID], obj[ID]))
        except Exception as e:
            if e.args[0] == 1062: pass # 1062 is what happens when you try to insert a duplicate row
            else:
                print(e)
                raise

            # }}}
    # {{{ unlink(obj): unlink the device from a storage daemon

    def unlink(self, obj):
        '''Remove the linkage between a Device and a Storage'''
        self.bc.do_sql(self._delete, (self[ID], obj[ID]))
        return

            # }}}
    # {{{ _cli_special_setup(): (un)link Storage

    def _cli_special_setup(self):
        '''Enable the CLI to (un)link devices to/from Sotrage Daemons.'''
        group = optparse.OptionGroup(self.parser, "Storage daemon links",
                                     "A device is associated with one or more storage daemons.")
        group.add_option('--add-link', metavar='STORAGE_DAEMON')
        group.add_option('--remove-link', metavar='STORAGE_DAEMON')
        self.parser.add_option_group(group)
        return

    # }}}
    # {{{ _cli_special_do_parse(args): (un)link Storage

    def _cli_special_do_parse(self, args):
        '''Handle any attempts by the CLI to (un)link the Device to/from Storage'''
        if args.add_link:
            s = bacula_tools.Storage().search(args.add_link)
            if not s[ID]: s.search(args.add_link)
            if not s[ID]:
                print('\n***WARNING***: Unable to find a Storage Daemon identified by "%s".  Not linked.\n' % args.add_link)
                return
            self.link(s)

        if args.remove_link:
            s = bacula_tools.Storage().search(args.remove_link)
            if not s[ID]: s.search(args.remove_link)
            if not s[ID]:
                print('\n***WARNING***: Unable to find a Storage Daemon identified by "%s".  Not unlinked.\n' % args.remove_link)
                return
            self.unlink(s)

        return

# }}}
    # {{{ _cli_special_print(): Display any linked Storage

    def _cli_special_print(self):
        '''Print any linked Storage'''
        for row in self.bc.do_sql(self._select, self[ID]):
            s = bacula_tools.Storage().search(row[0])
            print(('%'+ str(self._maxlen) + 's: %s') % ('Storage Daemon', s[NAME]))
        return

    # }}}
    # {{{ _cli_special_clone(oid): Handle cloning requirements.

    def _cli_special_clone(self, oid):
        '''Any clones of this device will be linked to the same Storage.'''
        for row in self.bc.do_sql(self._select, oid): self.bc.do_sql(self._insert, (self[ID], row[0]))
        return

        # }}}

def main():
    s = Device()
    s.cli()

if __name__ == "__main__": main()
