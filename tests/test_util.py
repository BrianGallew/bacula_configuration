from __future__ import print_function
import os
import sys
import pprint
import unittest
import pkg_resources
sys.path.insert(0, '..')
sys.path.insert(0, '.')
import bacula_tools
import mock
import socket


class generate_password_tests(unittest.TestCase):

    def test_length(self):
        self.assertEquals(len(bacula_tools.generate_password()), 44)
        return

    def test_length_set(self):
        self.assertEquals(len(bacula_tools.generate_password(22)), 22)
        return

    def test_password_uniqueness(self):
        self.assertNotEquals(
            bacula_tools.generate_password(), bacula_tools.generate_password())
        return


class die_tests(unittest.TestCase):

    def test_die(self):
        self.assertRaises(SystemExit, bacula_tools.die, 'just kidding')


class hostname_mangler_tests(unittest.TestCase):

    def test_exmample_com(self):
        self.assertEquals(
            bacula_tools.hostname_mangler('www.example.com'), 'www')
        return

    def test_exmample_net(self):
        self.assertEquals(
            bacula_tools.hostname_mangler('www.example.net'), 'www')
        return

    def test_exmample_io(self):
        self.assertEquals(
            bacula_tools.hostname_mangler('www.example.io'), 'www')
        return

    def test_four_parts(self):
        self.assertEquals(
            bacula_tools.hostname_mangler('www.here.example.net'), 'www.here')
        return

    def test_two_parts(self):
        self.assertEquals(
            bacula_tools.hostname_mangler('www.here'), 'www.here')
        return


class plist_tests(unittest.TestCase):

    def test_one_item(self):
        ts = 'one'
        obj = bacula_tools.PList(ts)
        res = obj[:]
        self.assertEquals([ts], res)
        return

    def test_two_items(self):
        ts = 'one two'
        obj = bacula_tools.PList(ts)
        res = obj[:]
        self.assertEquals(['one two', 'onetwo'], res)
        return

    def test_three_items(self):
        ts = 'one two three'
        obj = bacula_tools.PList(ts)
        res = obj[:]
        self.assertEquals(
            ['one two three', 'one twothree', 'onetwo three', 'onetwothree', ], res)
        return

    def test_four_items(self):
        ts = 'one two three four'
        obj = bacula_tools.PList(ts)
        res = obj[:]
        self.assertEquals(['one two three four', 'one two threefour', 'one twothree four', 'one twothreefour',
                           'onetwo three four', 'onetwo threefour', 'onetwothree four', 'onetwothreefour', ], res)
        return


class database_storage_tests(unittest.TestCase):

    def setUp(self):
        bacula_tools.MYSQL_DB = 'test'
        bacula_tools.MYSQL_HOST = 'localhost'
        bacula_tools.MYSQL_USER = 'test'
        bacula_tools.MYSQL_PASS = 'test'

        sql = pkg_resources.resource_string(
            'bacula_tools', 'data/bacula_configuration.schema').split(';')
        self.bc = bacula_tools.Bacula_Factory()
        self.bc.connect(
            database='test', host='localhost', user='test', passwd='test')
        foo = sys.stderr
        sys.stderr = open('/dev/null', 'w')

        for s in sql:
            s = s.strip()
            if not s:
                continue
            # if 'DROP TABLE' in s: continue
            row = self.bc.do_sql(s)
        self.client = bacula_tools.Client()
        self.client.set_name('Client')
        self.director = bacula_tools.Director()
        self.director.set_name('Director')
        sys.stderr = foo
        return

    def tearDown(self):
        sql = pkg_resources.resource_string(
            'bacula_tools', 'data/bacula_configuration.schema').split(';')
        foo = sys.stderr
        sys.stderr = open('/dev/null', 'w')
        for s in sql:
            s = s.strip()
            if not s:
                continue
            if not 'DROP TABLE' in s:
                continue
            #row = self.bc.do_sql(s)
        sys.stderr = foo
        return

    def test_no_password(self):
        self.bc.do_sql('delete from pwords')
        p = bacula_tools.PasswordStore(self.client, self.director)
        self.assertFalse(p.password)
        return

    def test_password_store_invalid(self):
        self.bc.do_sql('delete from pwords')
        p = bacula_tools.PasswordStore(self.client, self.director)
        p.store()
        self.assertRaises(AttributeError, p.store())
        return

    def test_password_store_valid(self):
        PWORD = 'fred'
        self.bc.do_sql('delete from pwords')
        p = bacula_tools.PasswordStore(self.client, self.director)
        p.password = PWORD
        p.store()
        result = self.bc.do_sql('''SELECT password FROM pwords WHERE obj_id=%s and obj_type=%s and director_id=%s and director_type=%s''', (self.client[
                                bacula_tools.ID], self.client.IDTAG, self.director[bacula_tools.ID], self.director.IDTAG))
        self.bc.do_sql('delete from pwords')
        self.assertEquals(result, ((PWORD,),))
        return

    def test_password_load(self):
        self.bc.do_sql('delete from pwords')
        self.bc.do_sql('''INSERT INTO pwords (obj_id, obj_type, director_id, director_type, password) values (%s, %s, %s, %s, %s)''', (self.client[
                       bacula_tools.ID], self.client.IDTAG, self.director[bacula_tools.ID], self.director.IDTAG, 'fred'))
        p = bacula_tools.PasswordStore(self.client, self.director)
        self.bc.do_sql('delete from pwords')
        self.assertEquals(p.password, 'fred')
        return

    def test_password_3_generage(self):
        p = bacula_tools.PasswordStore(self.client, self.director)
        p.password = bacula_tools.GENERATE
        p.store()
        p = bacula_tools.PasswordStore(self.client, self.director)
        self.bc.do_sql('delete from pwords')
        self.assertNotEquals(p.password, bacula_tools.GENERATE)
        return

    def test_default_jobs(self):
        bacula_tools.Messages().set_name('Standard')
        bacula_tools.Pool().set_name('Default')
        bacula_tools.Storage().set_name('File')
        bacula_tools.Schedule().set_name('Daily')
        bacula_tools.Fileset().set_name('FullUnix')
        bacula_tools.default_jobs(self.client)
        self.assertEquals(len(self.bc.do_sql('select * from jobs')), 1)
        self.bc.do_sql('delete from jobs')
        self.bc.do_sql('delete from storage')
        self.bc.do_sql('delete from schedules')
        self.bc.do_sql('delete from pools')
        self.bc.do_sql('delete from messages')
        self.bc.do_sql('delete from filesets')
        return

    def test_default_director_unspecified(self):
        bacula_tools.default_director(self.client)
        self.assertEquals(len(self.bc.do_sql('select * from pwords')), 1)
        self.bc.do_sql('delete from pwords')
        return

    def test_default_director_by_name(self):
        bacula_tools.default_director(
            self.client, self.director[bacula_tools.NAME])
        self.assertEquals(len(self.bc.do_sql('select * from pwords')), 1)
        self.bc.do_sql('delete from pwords')
        return

    def test_dbdict_delete(self):
        oldid = self.client[bacula_tools.ID]
        self.client.delete()
        self.client = bacula_tools.Client()
        self.client.set_name('Client')
        newid = self.client[bacula_tools.ID]
        self.assertNotEquals(oldid, newid)
        return

    def test_dbdict_set_boolean(self):
        self.client[bacula_tools.PKIENCRYPTION] = 0
        self.client.set(bacula_tools.PKIENCRYPTION, 'hi', boolean=True)
        self.assertEquals(self.client[bacula_tools.PKIENCRYPTION], 0)
        self.client.set(bacula_tools.PKIENCRYPTION, '1', boolean=True)
        result = self.bc.do_sql(
            'select pkiencryption from clients where id = %s', self.client[bacula_tools.ID])
        self.assertEquals(result[0][0], 1)
        self.client.set(bacula_tools.PKIENCRYPTION, 'off', boolean=True)
        result = self.bc.do_sql(
            'select pkiencryption from clients where id = %s', self.client[bacula_tools.ID])
        self.assertEquals(result[0][0], 0)
        self.client.set(bacula_tools.PKIENCRYPTION, 'yes', boolean=True)
        result = self.bc.do_sql(
            'select pkiencryption from clients where id = %s', self.client[bacula_tools.ID])
        self.assertEquals(result[0][0], 1)
        return

    def test_dbdict_set_password(self):
        self.director.set(bacula_tools.PASSWORD, 'fred')
        result = self.bc.do_sql(
            'select password from directors where id = %s', self.director[bacula_tools.ID])
        self.assertEquals(result[0][0], 'fred')
        self.director.set(bacula_tools.PASSWORD, bacula_tools.GENERATE)
        result = self.bc.do_sql(
            'select password from directors where id = %s', self.director[bacula_tools.ID])
        self.assertNotEquals(result[0][0], bacula_tools.GENERATE)
        return

    def test_dbdict_save_duplicate_record(self):
        oid = self.director[bacula_tools.ID]
        self.director[bacula_tools.ID] = None
        self.assertRaises(SystemExit, self.director._save)
        self.director[bacula_tools.ID] = oid
        return

    def test_dbdict_cli_option_processor(self):
        oid = self.director[bacula_tools.ID]
        self.director[bacula_tools.ID] = None
        self.assertRaises(SystemExit, self.director._save)
        self.director[bacula_tools.ID] = oid
        return


class guess_os_tests(unittest.TestCase):

    def test_default(self):
        self.assertEquals(bacula_tools.guess_os(), 'Linux')
        return

    def test_agent(self):
        os.environ[
            'HTTP_USER_AGENT'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.102 Safari/537.36'
        self.assertEquals(bacula_tools.guess_os(), 'OSX')
        del os.environ['HTTP_USER_AGENT']
        return

    def test_environ(self):
        os.environ['PATH_INFO'] = '/cgi-bin/webconfig/msie'
        self.assertEquals(bacula_tools.guess_os(), 'Windows')
        del os.environ['PATH_INFO']
        return


class die_tests(unittest.TestCase):

    def test_death(self):
        try:
            bacula_tools.die('Linux')
            assert('SystemExit not raised')
        except SystemExit:
            pass
        return


class guess_schedule_and_fileset_tests(unittest.TestCase):

    def test_default(self):
        self.assertEquals(bacula_tools.guess_schedule_and_filesets('localhost', 'BSD'),
                          bacula_tools.default_rules)
        return

    def test_hostname(self):
        self.assertEquals(bacula_tools.guess_schedule_and_filesets('origin31.example.com', 'BSD'),
                          [('SetOnHostGZIP', 'CustomHost'), ('XferLogs', 'FtpHosts')])
        return

    def test_os(self):
        self.assertEquals(bacula_tools.guess_schedule_and_filesets('localhost', 'Windows'),
                          [('WinFullGZIP', 'Weekly')])
        return

    def test_hostname_and_os(self):
        self.assertEquals(bacula_tools.guess_schedule_and_filesets('fred.ocs.example.com', 'Windows'),
                          [('SetOnHostGZIP', 'Weekly'), ('WinFullGZIP', 'Weekly')])
        return


class configfile_tests(unittest.TestCase):

    def setUp(self):
        self.testfile = '/tmp/testfile'
        self.contents = '''
        Now is the time
        for all good men
        (and women)
        to come to the aid
        of their country.'''
        return

    def tearDown(self):
        os.unlink(self.testfile)
        return

    def test_same_contents_close(self):
        c = bacula_tools.ConfigFile(self.testfile)
        c.close(self.contents)
        data = os.stat(self.testfile)
        c = bacula_tools.ConfigFile(self.testfile)
        self.assertFalse(c.close(self.contents))
        newdata = os.stat(self.testfile)
        self.assertEqual(data, newdata)
        return

    def test_no_file(self):
        c = bacula_tools.ConfigFile(self.testfile)
        self.assertTrue(c.close(self.contents))
        return

    def test_different_contents_close(self):
        c = bacula_tools.ConfigFile(self.testfile)
        c.close(self.contents)
        data = os.stat(self.testfile)
        c = bacula_tools.ConfigFile(self.testfile)
        self.assertTrue(c.close(self.contents + 'asdf'))
        newdata = os.stat(self.testfile)
        self.assertNotEqual(data, newdata)
        return


@mock.patch('socket.socket', autospec=True)
@mock.patch('sys.stderr', autospec=True)
class bsock_tests(unittest.TestCase):

    def test_init(self, stderr, sock):
        b = bacula_tools.BSock('foo', 'bar', 'me', 777)
        c = b.connection
        sock.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        c.assert_has_calls(
            [mock.call.settimeout(5), mock.call.connect(('foo', 777))])
        return

    def test_auth(self, stderr, sock):
        retstrings = [
            'auth cram-md5 <1.145269@foolishness>',
            '1000 OK auth\n',
            'ignored',
            '1000 OK auth\n',
        ]
        with mock.patch('bacula_tools.BSock.__init__', new=lambda x: None), mock.patch('bacula_tools.BSock.send', autospec=True), mock.patch('bacula_tools.BSock.recv', autospec=True, side_effect=retstrings):
            b = bacula_tools.BSock()
            b.password = 'unset'
            b.name = 'fred'
            b.auth()

        return

    def test_status(self, stderr, sock):
        sock.reset_mock()
        with mock.patch('bacula_tools.BSock.__init__', new=lambda x: None), mock.patch('bacula_tools.BSock.send',  new=sock), mock.patch('bacula_tools.BSock.recv_all', autospec=True, side_effect=['nothing', 'else']):
            b = bacula_tools.BSock()
            b.status()
            sock.assert_has_calls([mock.call.send('status')])
            sock.reset_mock()
            b.status('fred')
            sock.assert_has_calls([mock.call.send('.status fred')])
        sock.reset_mock()
        return

    def test_version(self, stderr, sock):
        sock.reset_mock()
        with mock.patch('bacula_tools.BSock.__init__', new=lambda x: None), mock.patch('bacula_tools.BSock.send',  new=sock), mock.patch('bacula_tools.BSock.recv', autospec=True, side_effect=['nothing', 'else']):
            b = bacula_tools.BSock()
            result = b.version()
            self.assertEquals(result, 'nothing')
            sock.assert_has_calls([mock.call.send('version')])
        sock.reset_mock()
        return
