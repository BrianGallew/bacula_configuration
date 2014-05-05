#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *  #pragma: no cover
import logging

class Client(DbDict):
    SETUP_KEYS = [
        ADDRESS, CATALOG_ID, FILERETENTION, JOBRETENTION, 
        WORKINGDIRECTORY, SDCONNECTTIMEOUT, MAXIMUMNETWORKBUFFERSIZE,
        PIDDIRECTORY, HEARTBEATINTERVAL, FDADDRESSES, FDADDRESS,
        FDSOURCEADDRESS, MAXIMUMBANDWIDTHPERJOB, PKIKEYPAIR, PKIMASTERKEY,
        NOTES,
        ]
    BOOL_KEYS = [AUTOPRUNE, PKIENCRYPTION, PKISIGNATURES]
    INT_KEYS = [(FDPORT, 9102), (MAXIMUMCONCURRENTJOBS, 1), PRIORITY]
    table = CLIENTS
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 2                   

    def __str__(self):
        '''Convert a Client into a string suitable for inclusion into a Director's configuration.'''
        self.output = ['Client {\n  Name = "%(name)s"' % self,'}']
        self.output.insert(-1, '  %s = "%s"' % (CATALOG.capitalize(), self._fk_reference(CATALOG_ID)[NAME]))
        if getattr(self,DIRECTOR_ID, None):
            a = PasswordStore(self, Director().search(self.director_id))
            if getattr(a, PASSWORD, None): self.output.insert(-1,'  Password = "%s"' % a.password)
        for key in [ADDRESS, FDPORT, FILERETENTION,
                    JOBRETENTION, MAXIMUMCONCURRENTJOBS,
                    MAXIMUMBANDWIDTHPERJOB, PRIORITY
                    ]:
            self._simple_phrase(key)
        self._yesno_phrase(AUTOPRUNE)
        return '\n'.join(self.output)

    def fd(self):
        '''Generate the Client configuration as appropriate for a file daemon'''
        self.output = ['Client {\n  Name = "%(name)s"' % self, '}']
        
        for key in [WORKINGDIRECTORY, PIDDIRECTORY, HEARTBEATINTERVAL, MAXIMUMCONCURRENTJOBS,
                    FDPORT, FDADDRESS, FDSOURCEADDRESS, SDCONNECTTIMEOUT,
                    MAXIMUMNETWORKBUFFERSIZE, MAXIMUMBANDWIDTHPERJOB, PKIKEYPAIR, PKIMASTERKEY
                    ]:
            self._simple_phrase(key)
        if self[FDADDRESSES]:
            self.output.insert(-1, '  %s {' % FDADDRESSES.capitalize())
            self.output.insert(-1,  self[FDADDRESSES])
            self.output.insert(-1, '  }')
        self._yesno_phrase(PKIENCRYPTION)
        self._yesno_phrase(PKISIGNATURES)
        return '\n'.join(self.output)

    def _cli_special_setup(self):
        '''This is *all* for setting the password.  Client passwords are associated
        with Directors, which in turn may or may not be monitors for this
        client, and different for other clients.  Look at the PasswordStore
        object in util.py for further detail.

        '''
        self._cli_parser_group(
            [PASSWORD, (DIRECTOR,None,'Director (name or ID) to associate with a password'), (MONITOR,None, '[yes|no]')],
            "Password set/change",
            "Passwords are associated with Directors, so changing a password requires "
            "that you specify the Director to which that password applies.  Also, Directors may be "
            "restricted to a monitoring role.  Specify a value of 'generate' for an auto-generated password."
            )
        return

    def _cli_special_do_parse(self, args):
        '''When setting the password, ensure that a Director is referenced.  If
        that's the case, make the appropriate updates.'''
        if (args.password == None) and (args.director == None): return # Nothing to do!
        if (args.password == None) ^ (args.director == None):
            print('\n***WARNING***: You must specify both a password and a director to change a password.  Password not changed.\n')
            return              # Bail on any password changes, but otherwise continue
        d = bacula_tools.Director().search(args.director)
        if not d[ID]:
            print('\n***WARNING***: Unable to find a director using "%s".  Password not changed\n' % args.director)
            return
        password = PasswordStore(self, d)
        password.password = args.password
        if args.monitor:
            if args.monitor.lower() in TRUE_VALUES: password.monitor = 1
            else: password.monitor = 0
        password.store()
        return

    def _cli_special_print(self):
        '''Prints out the passwords and the directors/consoles with which they are associated'''
        print('\nPasswords:')
        sql = 'select director_id, director_type from pwords where obj_id = %s and obj_type = %s'
        for row in self.bc.do_sql(sql, (self[ID], self.IDTAG)):
            if row[1] == Director.IDTAG: other = Director().search(row[0])
            if row[1] == Console.IDTAG: other = Console().search(row[0])
            password = PasswordStore(self, other)
            retval = '%30s: %s' % (other[NAME], password.password)
            print(retval)
        return

    def _cli_special_clone(self, old_id):
        '''When cloning a Client, assume that we want to also clone the passwords'''
        insert ='''INSERT INTO pwords (obj_id, obj_type, director_id, director_type, password)
                   SELECT %s, obj_type, director_id, director_type, password FROM pwords
                   WHERE obj_id=%s AND obj_type=%s'''
        self.bc.do_sql(insert, (self[ID], old_id, self.IDTAG))
        return

# Implement the CLI for managing Clients
def main():
    s = Client()
    s.cli()

if __name__ == "__main__": main()
