#! /usr/bin/env python

from __future__ import print_function
try:
    from . import *
except:
    from bacula_tools import *  # pragma: no cover
import logging


class Storage(DbDict):
    SETUP_KEYS = [SDPORT, ADDRESS, DEVICE, MEDIATYPE, MAXIMUMCONCURRENTJOBS, HEARTBEATINTERVAL,
                  WORKINGDIRECTORY, PIDDIRECTORY, CLIENTCONNECTWAIT, SDADDRESSES]
    BOOL_KEYS = [AUTOCHANGER, ALLOWCOMPRESSION]
    table = STORAGE
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 3
    dir_keys = [SDPORT, ADDRESS, DEVICE, MEDIATYPE,
                MAXIMUMCONCURRENTJOBS, HEARTBEATINTERVAL]
    sd_keys = [WORKINGDIRECTORY, PIDDIRECTORY, CLIENTCONNECTWAIT, SDADDRESSES,
               SDPORT, MAXIMUMCONCURRENTJOBS, HEARTBEATINTERVAL]

    def __str__(self):
        '''String representation of a Storage suitable for inclusion in a Director configuration.'''
        self.output = ['Storage {\n  Name = "%(name)s"' % self, '}']
        if getattr(self, bacula_tools.DIRECTOR_ID, None):
            a = PasswordStore(self, Director().search(self.director_id))
            if getattr(a, PASSWORD, None):
                self.output.insert(-1, '  Password = "%s"' % a.password)

        for key in self.dir_keys:
            self._simple_phrase(key)
        for key in self.BOOL_KEYS:
            self._simple_phrase(key)
        return '\n'.join(self.output)

    def sd(self):
        '''String representation of a Storage suitable for inclusion in a Storage configuration.'''
        self.output = ['Storage {\n  Name = "%(name)s"' % self, '}']
        for key in self.sd_keys:
            self._simple_phrase(key)
        # Special keys
        if self[ADDRESS]:
            self.output.insert(-1, '%sSDAddress = %s' %
                               (self.prefix, self[ADDRESS]))
        return '\n'.join(self.output)

    def _cli_special_setup(self):
        '''Add CLI switches for password handling.'''
        self._cli_parser_group(
            [PASSWORD, (DIRECTOR, None,
                        'Director (name or ID) to associate with a password')],
            "Password set/change",
            "Passwords are associated with directors, so changing a password requires "
            "that you specify the director to which that password applies.  Set the password to "
            "a value of 'generate' to auto-generate a password."
        )
        return

    def _cli_special_do_parse(self, args):
        '''Handle CLI switches for password management.'''
        if (args.password == None) and (args.director == None):
            return  # Nothing to do!
        if (args.password == None) ^ (args.director == None):
            print(
                '\n***WARNING***: You must specify both a password and a director to change a password.  Password not changed.\n')
            # Bail on any password changes, but otherwise continue
            return
        d = bacula_tools.Director()
        try:
            d.search(args.director)
        except:
            d.search(args.director)
        if not d[ID]:
            print(
                '\n***WARNING***: Unable to find a director using "%s".  Password not changed\n' % args.director)
            return
        password = PasswordStore(self, d)
        password.password = args.password
        password.store()
        return

    def _cli_special_print(self):
        '''Print out the passwords for the CLI.'''
        print('\nPasswords:')
        sql = 'select director_id, director_type from pwords where obj_id = %s and obj_type = %s'
        for row in self.bc.do_sql(sql, (self[ID], self.IDTAG)):
            if row[1] == Director.IDTAG:
                other = Director().search(row[0])
            if row[1] == Console.IDTAG:
                other = Console().search(row[0])
            password = PasswordStore(self, other)
            print('%30s: %s' % (other[NAME], password.password))
        return

    def _cli_special_clone(self, old_id):
        '''Storage clones should have the same sets of passwords as the source object.'''
        insert = '''INSERT INTO pwords (obj_id, obj_type, director_id, director_type, password)
                   SELECT %s, obj_type, director_id, director_type, password FROM pwords
                   WHERE obj_id=%s AND obj_type=%s;'''
        print(insert % (self[ID], old_id, self.IDTAG))
        self.bc.do_sql(insert, (self[ID], old_id, self.IDTAG))
        return

    def list_clients(self):
        '''List the clients with jobs that use this storage.'''
        sql = 'SELECT DISTINCT c.name FROM clients c, jobs j WHERE j.storage_id = %s and j.client_id = c.id'
        for host in self.bc.do_sql(sql, self[ID]):
            print(host[0])
        return

    def move(self, target_host):
        '''Change all jobs for target_host to use this Storage.'''
        client = Client().search(target_host)
        if not client[ID]:
            print('No such client:', target_host)
            return
        old_dests = [x[0] for x in self.bc.do_sql(
            'SELECT DISTINCT s.name FROM storage s, jobs j where j.client_id = %s and j.storage_id = s.id', client[ID])]
        if not old_dests:
            print('No jobs configured for client:', target_host)
            return
        retval = self.bc.do_sql(
            'UPDATE jobs SET storage_id = %s WHERE client_id = %s', (self[ID], client[ID]))
        print('Moved %s from %s to %s' %
              (target_host, ', '.join(old_dests), self[NAME]))
        pass


def main():
    s = Storage()
    s.cli()

if __name__ == "__main__":
    main()
