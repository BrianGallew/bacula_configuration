from __future__ import print_function
import os
import sys
import pprint
import unittest
import pkg_resources
sys.path.insert(0, '..')
sys.path.insert(0, '.')
import bacula_tools
import bacula_tools.parser_support


class overall_parser_tests(unittest.TestCase):

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
        return

    def test_import_fd_conf(self):
        retval = bacula_tools.parser_support.parser(
            open('/etc/bacula/bacula-fd.conf').read())
        self.assertIsInstance(retval, list)
        return

    def test_import_sd_conf(self):
        retval = bacula_tools.parser_support.parser(
            open('/etc/bacula/bacula-sd.conf').read())
        self.assertIsInstance(retval, list)
        return

    def test_import_dir_conf(self):
        retval = bacula_tools.parser_support.parser(
            open('/etc/bacula/bacula-dir.conf').read())
        self.assertIsInstance(retval, list)
        return
