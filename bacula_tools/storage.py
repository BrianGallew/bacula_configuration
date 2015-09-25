#! /usr/bin/env python

from __future__ import print_function, absolute_import
import bacula_tools
import logging


class Storage(bacula_tools.DbDict):
    SETUP_KEYS = [bacula_tools.SDPORT, bacula_tools.ADDRESS, bacula_tools.DEVICE, bacula_tools.MEDIATYPE,
                  bacula_tools.MAXIMUMCONCURRENTJOBS, bacula_tools.HEARTBEATINTERVAL,
                  bacula_tools.WORKINGDIRECTORY, bacula_tools.PIDDIRECTORY, bacula_tools.CLIENTCONNECTWAIT,
                  bacula_tools.SDADDRESSES]
    BOOL_KEYS = [bacula_tools.AUTOCHANGER, bacula_tools.ALLOWCOMPRESSION]
    table = bacula_tools.STORAGE
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 3
    dir_keys = [bacula_tools.SDPORT, bacula_tools.ADDRESS, bacula_tools.DEVICE, bacula_tools.MEDIATYPE,
                bacula_tools.MAXIMUMCONCURRENTJOBS, bacula_tools.HEARTBEATINTERVAL]
    sd_keys = [bacula_tools.WORKINGDIRECTORY, bacula_tools.PIDDIRECTORY, bacula_tools.CLIENTCONNECTWAIT,
               bacula_tools.SDADDRESSES, bacula_tools.SDPORT, bacula_tools.MAXIMUMCONCURRENTJOBS,
               bacula_tools.HEARTBEATINTERVAL]

    def __str__(self):
        '''String representation of a Storage suitable for inclusion in a Director configuration.'''
        self.output = ['Storage {\n  Name = "%(name)s"' % self, '}']
        if getattr(self, bacula_tools.DIRECTOR_ID, None):
            a = bacula_tools.PasswordStore(
                self, bacula_tools.Director().search(self.director_id))
            if getattr(a, bacula_tools.PASSWORD, None):
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
        if self[bacula_tools.ADDRESS]:
            self.output.insert(-1, '%sSDAddress = %s' %
                               (self.prefix, self[bacula_tools.ADDRESS]))
        return '\n'.join(self.output)

    def _cli_special_setup(self):
        '''Add CLI switches for password handling.'''
        self._cli_parser_group(
            [bacula_tools.PASSWORD, (bacula_tools.DIRECTOR, None,
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
        if not d[bacula_tools.ID]:
            print(
                '\n***WARNING***: Unable to find a director using "%s".  Password not changed\n' % args.director)
            return
        password = bacula_tools.PasswordStore(self, d)
        password.password = args.password
        password.store()
        return

    def _cli_special_print(self):
        '''Print out the passwords for the CLI.'''
        print('\nPasswords:')
        sql = 'select director_id, director_type from pwords where obj_id = %s and obj_type = %s'
        for row in self.bc.do_sql(sql, (self[bacula_tools.ID], self.IDTAG)):
            if row[1] == bacula_tools.Director.IDTAG:
                other = bacula_tools.Director().search(row[0])
            if row[1] == bacula_tools.Console.IDTAG:
                other = bacula_tools.Console().search(row[0])
            try:
                password = bacula_tools.PasswordStore(self, other)
                print('%30s: %s' %
                      (other[bacula_tools.NAME], password.password))
            except:
                # There's no password assiciated with this director/console.
                pass
        return

    def _cli_special_clone(self, old_id):
        '''Storage clones should have the same sets of passwords as the source object.'''
        insert = '''INSERT INTO pwords (obj_id, obj_type, director_id, director_type, password)
                   SELECT %s, obj_type, director_id, director_type, password FROM pwords
                   WHERE obj_id=%s AND obj_type=%s;'''
        print(insert % (self[bacula_tools.ID], old_id, self.IDTAG))
        self.bc.do_sql(insert, (self[bacula_tools.ID], old_id, self.IDTAG))
        return

    def list_clients(self):
        '''List the clients with jobs that use this storage.'''
        sql = '''SELECT DISTINCT c.name FROM clients c, jobs j
        WHERE j.client_id = c.id AND j.storage_id IN
        (SELECT s.id FROM storage s, storage t
        WHERE s.address = t.address AND t.id=%s AND NOT s.id = t.id);'''
        for host in self.bc.do_sql(sql, self[bacula_tools.ID]):
            print(host[0])
        return

    def move(self, target_host):
        '''Change all jobs for target_host to use this Storage.'''
        c = bacula_tools.Client().search(target_host)
        for job in bacula_tools.Job.Find(client_id=c[bacula_tools.ID]):
            pool_name = '%s-%s' % (self[bacula_tools.NAME],
                                   c[bacula_tools.FILERETENTION].replace(
                ' ', '_'))
            new_pool = bacula_tools.Pool().search(pool_name)
            job.set(bacula_tools.POOL_ID, new_pool[bacula_tools.ID])
            job_storage = bacula_tools.Storage().search(
                job[bacula_tools.STORAGE_ID])
            job_storage.set(
                bacula_tools.ADDRESS, self[bacula_tools.ADDRESS])
            job_device = bacula_tools.Device().search(
                job_storage[bacula_tools.NAME])
            old_storage = job_device.find_linked()
            if old_storage:
                for o_s in old_storage:
                    job_device.unlink(o_s)
                print('Moved %s from %s to %s' %
                      (target_host, o_s[bacula_tools.NAME], self[bacula_tools.NAME]))
            job_device.link(self)
        pass


def main():
    s = Storage()
    s.cli()

if __name__ == "__main__":
    main()
