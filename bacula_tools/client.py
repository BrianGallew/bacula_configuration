#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''Bacula client (bacula-fd) definition handling.
'''
from __future__ import print_function, absolute_import
import bacula_tools
import logging
logger = logging.getLogger(__name__)


class Client(bacula_tools.DbDict):

    '''Object to handle storage and output of Bacula client objects.  It's a
    little complicated because bacula uses multiple names to refer to it,
    as well as there being a lot of options.
    '''
    SETUP_KEYS = [bacula_tools.ADDRESS, bacula_tools.CATALOG_ID,
                  bacula_tools.FILERETENTION, bacula_tools.JOBRETENTION,
                  bacula_tools.WORKINGDIRECTORY, bacula_tools.SDCONNECTTIMEOUT,
                  bacula_tools.MAXIMUMNETWORKBUFFERSIZE, bacula_tools.PIDDIRECTORY,
                  bacula_tools.HEARTBEATINTERVAL, bacula_tools.FDADDRESSES,
                  bacula_tools.FDADDRESS, bacula_tools.FDSOURCEADDRESS,
                  bacula_tools.MAXIMUMBANDWIDTHPERJOB, bacula_tools.PKIKEYPAIR,
                  bacula_tools.PKIMASTERKEY, bacula_tools.NOTES]
    BOOL_KEYS = [bacula_tools.AUTOPRUNE, bacula_tools.PKIENCRYPTION,
                 bacula_tools.PKISIGNATURES]
    INT_KEYS = [(bacula_tools.FDPORT, 9102),
                (bacula_tools.MAXIMUMCONCURRENTJOBS, 1), bacula_tools.PRIORITY]
    table = bacula_tools.CLIENTS
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 2

    def __str__(self):
        '''Convert a Client into a string suitable for inclusion into a Director's
configuration.'''
        self.output = ['Client {\n  Name = "%(name)s"' % self, '}']
        self.output.insert(-1, ' %s = "%s"' %
                           (bacula_tools.CATALOG.capitalize(),
                            self._fk_reference(bacula_tools.CATALOG_ID)[bacula_tools.NAME]))
        if getattr(self, bacula_tools.DIRECTOR_ID, None):
            pw_store = bacula_tools.PasswordStore(
                self, bacula_tools.Director().search(self.director_id))
            if getattr(pw_store, bacula_tools.PASSWORD, None):
                self.output.insert(-1, '  Password = "%s"' % pw_store.password)
        for key in [bacula_tools.ADDRESS, bacula_tools.FDPORT,
                    bacula_tools.FILERETENTION, bacula_tools.JOBRETENTION,
                    bacula_tools.MAXIMUMCONCURRENTJOBS,
                    bacula_tools.MAXIMUMBANDWIDTHPERJOB,
                    bacula_tools.PRIORITY]:
            self._simple_phrase(key)
        self._yesno_phrase(bacula_tools.AUTOPRUNE)
        return '\n'.join(self.output)

    def fd(self):
        '''Generate the Client configuration as appropriate for a file daemon'''
        self.output = ['Client {\n  Name = "%(name)s"' % self, '}']

        for key in [bacula_tools.WORKINGDIRECTORY,
                    bacula_tools.PIDDIRECTORY,
                    bacula_tools.HEARTBEATINTERVAL,
                    bacula_tools.MAXIMUMCONCURRENTJOBS,
                    bacula_tools.FDPORT, bacula_tools.FDADDRESS,
                    bacula_tools.FDSOURCEADDRESS,
                    bacula_tools.SDCONNECTTIMEOUT,
                    bacula_tools.MAXIMUMNETWORKBUFFERSIZE,
                    bacula_tools.MAXIMUMBANDWIDTHPERJOB,
                    bacula_tools.PKIKEYPAIR, bacula_tools.PKIMASTERKEY]:
            self._simple_phrase(key)
        if self[bacula_tools.FDADDRESSES]:
            self.output.insert(-1, '  %s {' %
                               bacula_tools.FDADDRESSES.capitalize())
            self.output.insert(-1, self[bacula_tools.FDADDRESSES])
            self.output.insert(-1, '  }')
        self._yesno_phrase(bacula_tools.PKIENCRYPTION)
        self._yesno_phrase(bacula_tools.PKISIGNATURES)
        return '\n'.join(self.output)

    def _cli_special_setup(self):
        '''This is *all* for setting the password.  Client passwords are associated
        with Directors, which in turn may or may not be monitors for this
        client, and different for other clients.  Look at the PasswordStore
        object in util.py for further detail.

        '''
        self._cli_parser_group(
            [bacula_tools.PASSWORD, (bacula_tools.DIRECTOR,
                                     None, 'Director (name or ID) to associate with a password'),
             (bacula_tools.MONITOR, None, '[yes|no]')],
            "Password set/change",
            "Passwords are associated with Directors, so changing a password requires "
            "that you specify the Director to which that password applies.  Also, Directors may be "
            "restricted to a monitoring role.  Specify a value of 'generate' for an"
            "auto-generated password."
        )
        return

    def _cli_special_do_parse(self, args):
        '''When setting the password, ensure that a Director is referenced.  If
        that's the case, make the appropriate updates.'''
        if (args.password == None) and (args.director == None):
            return  # Nothing to do!
        if (args.password == None) ^ (args.director == None):
            logger.warning(
                'You must specify both a password and a director to change a password.  No change.')
            # Bail on any password changes, but otherwise continue
            return
        the_director = bacula_tools.Director().search(args.director)
        if not the_director[bacula_tools.ID]:
            logger.warning(
                'Unable to find a director using "%s".  No change.',
                args.director)
            return
        password = bacula_tools.PasswordStore(self, the_director)
        password.password = args.password
        if args.monitor:
            if args.monitor.lower() in bacula_tools.TRUE_VALUES:
                password.monitor = 1
            else:
                password.monitor = 0
        password.store()
        return

    def _cli_special_print(self):
        '''Prints out the passwords and the directors/consoles with which they are associated'''
        print('\nPasswords:')
        sql = 'select director_id, director_type from pwords where obj_id = %s and obj_type = %s'
        for row in self.bc.do_sql(sql, (self[bacula_tools.ID], self.IDTAG)):
            if row[1] == bacula_tools.Director.IDTAG:
                other = bacula_tools.Director().search(row[0])
            if row[1] == bacula_tools.Console.IDTAG:
                other = bacula_tools.Console().search(row[0])
            password = bacula_tools.PasswordStore(self, other)
            retval = '%30s: %s' % (other[bacula_tools.NAME], password.password)
            print(retval)
        return

    def _cli_special_clone(self, old_id):
        '''When cloning a Client, assume that we want to also clone the passwords'''
        insert = '''INSERT INTO pwords (obj_id, obj_type, director_id, director_type, password)
                   SELECT %s, obj_type, director_id, director_type, password FROM pwords
                   WHERE obj_id=%s AND obj_type=%s'''
        self.bc.do_sql(insert, (self[bacula_tools.ID], old_id, self.IDTAG))
        return

# Implement the CLI for managing Clients
def main():
    s = Client()
    s.cli()

if __name__ == "__main__":
    main()
