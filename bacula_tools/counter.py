#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (CATALOG_ID, COUNTER_ID, COUNTERS, DbDict, ID,
                          MINIMUM, MAXIMUM)
import bacula_tools
import logging


class Counter(DbDict):

    '''This is for configuring a counter.
    '''
    SETUP_KEYS = [CATALOG_ID, COUNTER_ID]
    INT_KEYS = [MINIMUM, MAXIMUM]
    table = COUNTERS

    def __str__(self):
        self.output = ['Counter {\n  Name = "%(name)s"' % self, '}']

        for key in self.INT_KEYS:
            self._simple_phrase(key)
        if self[CATALOG_ID] != None:
            self.output.insert(-1, '  %s = "%s"' %
                               (CATALOG.capitalize(), self._fk_reference(CATALOG_ID)[NAME]))
        if self[COUNTER_ID] != None:
            self.output.insert(-1, '  Wrap Counter = "%s"' %
                               self._fk_reference(COUNTER_ID)[NAME])

        return '\n'.join(self.output)


def main():  # Implement the CLI for managing Counters
    s = Counter()
    s.cli()

if __name__ == "__main__":
    main()
