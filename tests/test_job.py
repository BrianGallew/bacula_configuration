#! /usr/bin/env python

from __future__ import print_function
import os, sys, unittest, pkg_resources, mock, logging
sys.path.insert(0, '..')
sys.path.insert(0, '.')
import bacula_tools, bacula_tools.bacula_config

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

    test_cases = ['''  Name = "BackupClient1"
      JobDefs = "DefaultJob"

    ''',
                  '''  Name = "BackupClient2"
      Client = outbidoverdrive.gallew.org2-fd
      RunBeforeJob = "/usr/local/Cellar/bacula/5.2.13/etc/make_catalog_backup.pl MyCatalog"
      JobDefs = "DefaultJob"

    ''',
                  '''  Name = "BackupCatalog"
      JobDefs = "DefaultJob"
      Level = Full
      FileSet="Catalog"
      Schedule = "WeeklyCycleAfterBackup"
      RunBeforeJob = "kiss butt goodbye"
      Write Bootstrap = "/usr/local/Cellar/bacula/5.2.13/opt/bacula/working/%n.bsr"
      Priority = 11

    ''',
                  '''  Name = "RestoreFiles"
      Type = Restore
      Client=outbidoverdrive.gallew.org-fd                 
      FileSet="Full Set"                  
      Storage = File                      
      Pool = Default
      Messages = Standard
      Where = /tmp/bacula-restores
      RunAfterJob  = "/usr/local/Cellar/bacula/5.2.13/etc/delete_catalog_backup"
    ''',
                  '''  Name = "Clever Test"
      Client=outbidoverdrive.gallew.org-fd                 
      FileSet="Full Set"                  
      Storage = File                      
      Pool = Default
      Run Script {
        Command = "clever script"
        Runswhen = "Before"
        Runsonclient = No
      }
      Messages = Standard
      Where = /tmp/bacula-restores
    ''',
                  '''
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
            }''',

    ]
    # def setUp(self):
    #     self.db = mock.MagicMock()
    #     mock.patch('bacula_tools.Job.bc', new=self.db)
    #     return

    def test_delete_script(self): pass
        
    def test_parser_simplest(self):
        retstrings = ['1', '2', '3']
        m = mock.MagicMock()
        m.value_ensure.return_value=[{bacula_tools.NAME: 'fred', bacula_tools.ID:1}, ()]
        with mock.patch('bacula_tools.Job.bc', new=m):
            j = bacula_tools.Job()
            j.parse_string('''Name = fred''')
            logging.warning(m.mock_calls)
            m.value_ensure.assert_called_once_with('jobs', 'name', 'fred', asdict=True)
