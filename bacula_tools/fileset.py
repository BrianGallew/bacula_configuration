from . import *
from re import compile, MULTILINE, IGNORECASE, DOTALL

class Fileset(DbDict):
    table = FILESETS
    SETUP_KEYS = [(VSSENABLED, 1),
                  (IGNORECHANGES, 0),
                  (ENTRIES, [])
        ]
    # {{{ _load_parts(): helper for loading self from the database

    def _load_parts(self):
        sql = '''SELECT b.id AS id, b.name AS name, b.option, a.exclude
                 FROM fileset_link a, fileset_files b
                 WHERE a.file_id = b.id AND a.fileset_id = %s'''
        self[ENTRIES] = list(self.bc.do_sql(sql, self[ID]))
        return self

    # }}}
    # {{{ _parse_add_entry(*args): adds various entries into this fileset

    def _parse_add_entry(self, *args):
        trim = args[2]
        if trim[0] == EXCLUDE: exclude=1
        else: exclude=0
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

    # }}}
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_name = Keyword('name', caseless=True) + gr_eq + gr_opt_quoted_string
        gr_name.setParseAction(lambda x, y=self: y._set_name(x[2]))
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))
        gr_phrase = Group(OneOrMore(gr_stripped_string | Word(alphanums)) + gr_eq + gr_opt_quoted_string)
        gr_ifsc = Group(Keyword('Ignore FileSet Changes', caseless=True) | Keyword('IgnoreFileSetChanges', caseless=True) | Keyword('Ignore FileSetChanges', caseless=True) | Keyword('IgnoreFileSetChanges', caseless=True)) + gr_eq + gr_yn.copy().addParseAction(lambda *x: self._set(IGNORECHANGES, int(x[2][0])))
        gr_evss = Group(Keyword('Enable VSS', caseless=True) | Keyword('EnableVSS', caseless=True)) + gr_eq + gr_yn.copy().addParseAction(lambda *x: self._set(VSSENABLED, int(x[2][0])))

        gr_i_option = Group(Keyword('options', caseless=True) + nestedExpr('{','}', Regex('[^\}]+', re.MULTILINE)))
        gr_e_option = gr_i_option.copy()
        gr_i_file = gr_phrase.copy()
        gr_e_file = gr_phrase.copy()

        gr_inc = Keyword('include', caseless=True) + nestedExpr('{','}', OneOrMore(gr_i_option | gr_i_file))
        gr_inc.addParseAction(self._parse_add_entry)
        gr_exc = Keyword('exclude', caseless=True) + nestedExpr('{','}', OneOrMore(gr_e_option | gr_e_file))
        gr_exc.addParseAction(self._parse_add_entry)

        gr_res = OneOrMore(gr_name | gr_inc | gr_exc | gr_ifsc | gr_evss)
        result = gr_res.parseString(string, parseAll=True)
        return 'Fileset: ' + self[NAME]

    # }}}
    # {{{ _add_entry(entry, option, exclude): add another entry

    def _add_entry(self, entry, option, exclude):
        '''The logic here could bite you if it were legal to have an option
        and a file with the same content.
        '''
        new_entry = list(self.bc.value_ensure(FILESET_FILES, NAME, entry)[0])
        if not new_entry[2] == option:
            new_entry[2] = option
            list(self.bc.do_sql('UPDATE fileset_files SET `option` = %s WHERE id = %s', (new_entry[2], new_entry[0])))

        new_entry.append(exclude)
        row = self.bc.do_sql('SELECT * FROM fileset_link WHERE fileset_id = %s AND file_id = %s and exclude = %s',
                             (self[ID], new_entry[0], new_entry[3]))
        if not row:
            try: self.bc.do_sql('INSERT INTO fileset_link(fileset_id, file_id, exclude) VALUES (%s, %s, %s)',
                           (self[ID], new_entry[0], new_entry[3]))
            except: print('You may not have the same entry in both Include{} and Exclude{} clauses.')

        self._load_parts()
        return

    # }}}
    # {{{ _delete_entry(entry): delete an entry

    def _delete_entry(self, entry):
        for row in self[ENTRIES]:
            if not row[1] == entry: continue
            self.bc.do_sql('DELETE FROM fileset_link WHERE fileset_id = %s AND file_id = %s and exclude = %s',
                           (self[ID], row[0], row[3]))
            self[ENTRIES].remove(row)
            return
        print('I cannot delete entries that do not exist!')
        return

    # }}}
    # {{{ _set_name(name): set my name

    def _set_name(self, name):
        self.bc = Bacula_Factory()
        row = self.bc.value_ensure(FILESETS, NAME, name.strip())[0]
        self[NAME] = row[1]
        self[ID] = row[0]
        changed = self[VSSENABLED] ^ row[2]
        if changed: self[VSSENABLED] = 0
        changed2 = self[IGNORECHANGES] ^ row[3]
        if changed2: self[IGNORECHANGES] = 1
        if changed | changed2: self._save()
        return

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Fileset {','  Name = "%(name)s"' % self, '}']
        self._yesno_phrase(VSSENABLED)
        self._yesno_phrase(IGNORECHANGES)
        for test,phrase in ([0,'Include'],[1,'Exclude']):
            subset =  [x for x in self[ENTRIES] if x[3] == test]
            if subset:              # We have includes
                self.output.insert(-1, '  %s {' % phrase)
                options = [x for x in subset if x[2]]
                if options:
                    self.output.insert(-1,'    Options {')
                    [self.output.insert(-1,'      ' + x[1]) for x in options]
                    self.output.insert(-1,'    }')
                [self.output.insert(-1,'    %s' % x[1]) for x in subset if not x[2]]
                self.output.insert(-1,'  }')
        return '\n'.join(self.output)

# }}}
    # {{{ _save(): Save the top-level fileset record
    def _save(self):
        return self.bc.do_sql('update %s set %s = %%s, %s = %%s, %s = %%s where id = %%s' % (FILESETS, NAME, VSSENABLED, IGNORECHANGES),
                              (self[NAME], self[VSSENABLED], self[IGNORECHANGES], self[ID]))
# }}}
        
