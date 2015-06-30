#! /usr/bin/env python

from __future__ import print_function
import os
import sys
import unittest
import pkg_resources
import mock
import logging
sys.path.insert(0, '..')
sys.path.insert(0, '.')
import bacula_tools
import bacula_tools.bacula_config
import bacula_tools.parser_support


@mock.patch('bacula_tools.Job.bc')
class job_tests(unittest.TestCase):

    silliness = '''  Name = "DefaultJob"
      Type = Backup
      Level = Incremental
      Client = outbidoverdrive.gallew.org-fd 
      FileSet = "Full Set"
      Schedule = "WeeklyCycle"
      Storage = File
      Messages = Standard
      Pool = File
      Priority = 10
      Write Bootstrap = "/usr/local/Cellar/bacula/5.2.13/opt/bacula/working/%c.bsr"
    '''

    full_case = '''
    Name = zabbix-db02-FullSnap
      Client = zabbix-db02
      Enabled = yes
      Storage = zabbix-db02-FullSnap
      Write Bootstrap = "/var/db/bacula/zabbix-db02FullSnap.bsr"
      Priority = 10
      Maximum Concurrent Jobs = 1
      Type = Backup
      Level = Incremental
      FileSet = FullSnap
      Schedule = DaytimeWeeklyFull
      Messages = Standard
      Pool = bs-sd002
      Rerun Failed Levels = yes
      Allow Mixed Priority = yes
            Run Script {
                    Command = "/usr/local/llnw/mysql/backup_begin.sh"
                    RunsWhen = Before
                    RunsOnFailure = No
                    RunsOnClient = Yes
                    FailJobOnError = Yes
            }
            Run Script {
                    Command = "/usr/local/llnw/mysql/backup_end.sh"
                    RunsWhen = After
                    RunsOnFailure = No
                    RunsOnClient = Yes
            }
            Run Script {
                    Command = "/usr/local/llnw/mysql/backup_fail.sh"
                    RunsWhen = After
                    RunsOnFailure = yes
                    RunsOnClient = Yes
                    RunsOnSuccess = No
            }'''

    def test_delete_script(self, m): pass

    def test_parser_simplest(self, m):
        retstrings = ['1', '2', '3']
        m.value_ensure.return_value = [
            {bacula_tools.NAME: 'fred', bacula_tools.ID: 1}, ()]
        j = bacula_tools.Job()
        j.parse_string('''Name = fred''')
        logging.warning(m.mock_calls)
        m.value_ensure.assert_called_once_with(
            'jobs', 'name', 'fred', asdict=True)

    def test_parser_more(self, m):
        logging.root.setLevel(logging.INFO)
        retstrings = ['1', '2', '3']
        m.value_ensure.return_value = [{bacula_tools.NAME: 'fred', bacula_tools.ID: 1},
                                       {bacula_tools.NAME: 'script1',
                                           bacula_tools.ID: 2},
                                       {bacula_tools.NAME: 'script2',
                                           bacula_tools.ID: 3},
                                       {bacula_tools.NAME: 'script3', bacula_tools.ID: 4}, ()]
        s = mock.MagicMock()
        s.search.return_value = [{bacula_tools.NAME: 'script1', bacula_tools.ID: 2},
                                 {bacula_tools.NAME: 'script2',
                                     bacula_tools.ID: 3},
                                 {bacula_tools.NAME: 'script3',
                                     bacula_tools.ID: 4},
                                 {bacula_tools.NAME: 'script1',
                                     bacula_tools.ID: 2},
                                 {bacula_tools.NAME: 'script2',
                                     bacula_tools.ID: 3},
                                 {bacula_tools.NAME: 'script3',
                                     bacula_tools.ID: 4},
                                 {bacula_tools.NAME: 'script1',
                                     bacula_tools.ID: 2},
                                 {bacula_tools.NAME: 'script2',
                                     bacula_tools.ID: 3},
                                 {bacula_tools.NAME: 'script3',
                                     bacula_tools.ID: 4},
                                 {bacula_tools.NAME: 'script1',
                                     bacula_tools.ID: 2},
                                 {bacula_tools.NAME: 'script2',
                                     bacula_tools.ID: 3},
                                 {bacula_tools.NAME: 'script3',
                                     bacula_tools.ID: 4},
                                 {bacula_tools.NAME: 'script1',
                                     bacula_tools.ID: 2},
                                 {bacula_tools.NAME: 'script2',
                                     bacula_tools.ID: 3},
                                 {bacula_tools.NAME: 'script3',
                                     bacula_tools.ID: 4},
                                 ]

        expected_call_list = [mock.call('SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (1, 7L)),
                              mock.call(
                                  'SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (1, 8L)),
                              mock.call(
                                  'SELECT * FROM job_scripts WHERE job_id = %s AND script_id = %s', (1, 9L)),
                              ]

        with mock.patch('bacula_tools.Job._load_scripts'), mock.patch('bacula_tools.Job.search'), mock.patch('bacula_tools.Job.set'), mock.patch('bacula_tools.Job._parse_script', new=s):
            bacula_tools.parser_support.setup_for_parsing()
            j = bacula_tools.Job()
            j.parse_string(self.full_case)
            print(s.called)
            self.assertEquals(m.do_sql.call_args_list, expected_call_list)
