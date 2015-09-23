#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (ACTIONONPURGE, AUTOPRUNE, CATALOGFILES,
                          CLEANINGPREFIX, DbDict, FILERETENTION,
                          JOBRETENTION, LABELFORMAT, MAXIMUMVOLUMEBYTES,
                          MAXIMUMVOLUMEFILES, MAXIMUMVOLUMEJOBS,
                          MAXIMUMVOLUMES, POOLS, POOLTYPE,
                          PURGEOLDESTVOLUME, RECYCLE,
                          RECYCLECURRENTVOLUME, RECYCLEOLDESTVOLUME,
                          RECYCLEPOOL, SCRATCHPOOL, STORAGE_ID,
                          USEVOLUMEONCE, VOLUMERETENTION,
                          VOLUMEUSEDURATION, )
import logging


class Pool(DbDict):
    BOOL_KEYS = [AUTOPRUNE, CATALOGFILES, RECYCLE, USEVOLUMEONCE,
                 RECYCLEOLDESTVOLUME, RECYCLECURRENTVOLUME, PURGEOLDESTVOLUME]
    SETUP_KEYS = [MAXIMUMVOLUMES, MAXIMUMVOLUMEJOBS, MAXIMUMVOLUMEFILES,
                  MAXIMUMVOLUMEBYTES, VOLUMEUSEDURATION, VOLUMERETENTION,
                  ACTIONONPURGE, SCRATCHPOOL, RECYCLEPOOL,
                  FILERETENTION, JOBRETENTION, CLEANINGPREFIX,
                  LABELFORMAT, (POOLTYPE, 'Backup', "Enum: ['Backup', 'Archive', 'Cloned', 'Migration', 'Copy', 'Save']")]
    REFERENCE_KEYS = [STORAGE_ID, ]
    table = POOLS

    def __str__(self):
        '''String representation of a Pool formatted for inclusion in a config file.'''
        self.output = ['Pool {\n  Name = "%(name)s"' % self, '}']
        for key in self.SETUP_KEYS:
            self._simple_phrase(key, quoted=False)
        for key in self.BOOL_KEYS:
            self._yesno_phrase(key)
        for key in self.REFERENCE_KEYS:
            if self[key] == None:
                continue
            self.output.insert(-1, '  %s = "%s"' %
                               (key.replace('_id', '').capitalize(), self._fk_reference(key)[NAME]))

        return '\n'.join(self.output)


def main():
    s = Pool()
    s.cli()

if __name__ == "__main__":
    main()
