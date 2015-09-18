#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from bacula_tools import (DbDict, ENABLEVSS, EXCLUDE, FILESETS,
                          FILESET_FILES, ID, IGNOREFILESETCHANGES, OPTIONS,
                          NAME)
from re import compile, MULTILINE, IGNORECASE, DOTALL
import optparse
import logging


class Fileset(DbDict):
    table = FILESETS
    BOOL_KEYS = [ENABLEVSS, IGNOREFILESETCHANGES, ]

    def __init__(self, row={}, string=None):
        DbDict.__init__(self, row, string)
        self.entries = []
        return

    def _load_parts(self):
        '''Load up the rules from the table.'''
        if not self[ID]:
            return
        sql = '''SELECT b.id AS id, b.name AS name, b.option, a.exclude
                 FROM fileset_link a, fileset_files b
                 WHERE a.file_id = b.id AND a.fileset_id = %s'''
        self.entries = list(self.bc.do_sql(sql, self[ID]))
        return self

    def _parse_add_entry(self, *args):
        '''Supports the string parser.  Extracts fileset Include/Exclude phrases.
        This should probably be thrown back into the parser, but I'll leave
        that for a later effort.  For now, it works just fine.
        '''
        trim = args[2]
        if trim[0] == EXCLUDE:
            exclude = 1
        else:
            exclude = 0
        trim = trim[1]
        flag = args[2][0][0]
        data = args[2][0][1][0].strip()
        for row in trim:
            flag = row[0]
            if row[0] == OPTIONS:
                for opt in row[1][0].strip().split('\n'):
                    self._add_entry(opt.strip(), 1, exclude)
            else:
                self._add_entry(' '.join([x.strip() for x in row]), 0, exclude)
        return

    def _add_entry(self, entry, option=0, exclude=0):
        '''This holds the SQL that manages writing entries.  It probably needs a
        complete redesign.

        The logic here could bite you if it were legal to have an option
        and a file with the same content.

        '''
        new_entry = list(self.bc.value_ensure(FILESET_FILES, NAME, entry)[0])
        if not new_entry[2] == option:
            new_entry[2] = option
            list(self.bc.do_sql(
                'UPDATE fileset_files SET `option` = %s WHERE id = %s', (new_entry[2], new_entry[0])))

        new_entry.append(exclude)
        row = self.bc.do_sql('SELECT * FROM fileset_link WHERE fileset_id = %s AND file_id = %s and exclude = %s',
                             (self[ID], new_entry[0], new_entry[3]))
        if not row:
            try:
                self.bc.do_sql('INSERT INTO fileset_link(fileset_id, file_id, exclude) VALUES (%s, %s, %s)',
                               (self[ID], new_entry[0], new_entry[3]))
            except:
                print(
                    'You may not have the same entry in both Include{} and Exclude{} clauses.')

        self._load_parts()
        return

    def _delete_entry(self, entry):
        '''Remove an entry.'''
        for row in self.entries:
            if not row[1] == entry:
                continue
            self.bc.do_sql('DELETE FROM fileset_link WHERE fileset_id = %s AND file_id = %s and exclude = %s',
                           (self[ID], row[0], row[3]))
            self.entries.remove(row)
            return
        print('I cannot delete entries that do not exist!')
        return

    def __str__(self):
        '''Stringify into a form suitable for dropping into a Director configuration.'''
        self.output = ['Fileset {', '  Name = "%(name)s"' % self, '}']
        for key in self.BOOL_KEYS:
            self._yesno_phrase(key)

        for test, phrase in ([0, 'Include'], [1, 'Exclude']):
            subset = [x for x in self.entries if x[3] == test]
            if subset:              # We have includes
                self.output.insert(-1, '  %s {' % phrase)
                options = [x for x in subset if x[2]]
                if options:
                    self.output.insert(-1, '    Options {')
                    [self.output.insert(-1, '      ' + x[1]) for x in options]
                    self.output.insert(-1, '    }')
                [self.output.insert(-1, '    File = "%s"' % x[1])
                 for x in subset if not x[2]]
                self.output.insert(-1, '  }')
        return '\n'.join(self.output)

    def _cli_special_setup(self):
        '''Add CLI options to add file/option inclusion/exclusion rules.'''
        group = optparse.OptionGroup(self.parser,
                                     "Stanzas",
                                     "Handle elements of the Include and Exclude sections")
        group.add_option('--add-file', action='append',
                         default=[], help='Add a file to the Include section')
        group.add_option('--add-option', action='append',
                         default=[], help='Add an option to the Include section')
        group.add_option('--add-exclusion-file', action='append',
                         default=[], help='Add a file to the Exclude section')
        group.add_option('--add-exclusion-option', action='append',
                         default=[], help='Add an option to the Exclude section')
        group.add_option('--remove', action='append', default=[],
                         help='Removes exact text match for either an option or a file')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''Handle the args for adding/removing entries'''
        for stanza in args.add_file:
            self._add_entry(stanza, 0, 0)
        for stanza in args.add_option:
            self._add_entry(stanza, 1, 0)
        for stanza in args.add_exclusion_file:
            self._add_entry(stanza, 0, 1)
        for stanza in args.add_exclusion_option:
            self._add_entry(stanza, 1, 1)
        for stanza in args.remove:
            self._delete_entry(stanza)
        return

    def _cli_special_print(self):
        '''Print out the Inclusion and Exclusion rules'''
        fmt = '%' + str(self._maxlen) + 's: %s'
        for test, phrase in ([0, 'Include'], [1, 'Exclude']):
            subset = [x for x in self.entries if x[3] == test]
            if subset:              # We have a group!
                print(phrase)
                options = [x for x in subset if x[2]]
                if options:
                    print(fmt % ('Options', ','.join([x[1] for x in options])))
                [print(fmt % ('', x[1])) for x in subset if not x[2]]

    def _cli_special_clone(self, oid):
        '''When cloning, ensure that all of the rules get copied into the cloned Fileset.'''
        select = 'SELECT %s,file_id, exclude FROM fileset_link WHERE fileset_id = %%s' % self[
            ID]
        insert = 'INSERT INTO fileset_link (fileset_id,file_id,exclude) VALUES (%s,%s,%s)'
        for row in self.bc.do_sql(select, oid):
            self.bc.do_sql(insert, row)
        self._load_parts()
        return


def main():
    s = Fileset()
    s.cli()

if __name__ == "__main__":
    main()
