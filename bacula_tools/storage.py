#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Storage(DbDict):
    SETUP_KEYS = [SDPORT, ADDRESS, DEVICE, MEDIATYPE, MAXIMUMCONCURRENTJOBS, HEARTBEATINTERVAL,
                 WORKINGDIRECTORY, PIDDIRECTORY, CLIENTCONNECTWAIT, SDADDRESSES]
    BOOL_KEYS = [AUTOCHANGER, ALLOWCOMPRESSION]
    table = STORAGE
    # This is kind of a hack used for associating Messages with different
    # resources that are otherwise identically named/numbered.
    IDTAG = 3
    dir_keys = [SDPORT, ADDRESS, DEVICE, MEDIATYPE, MAXIMUMCONCURRENTJOBS, HEARTBEATINTERVAL]
    sd_keys = [WORKINGDIRECTORY, PIDDIRECTORY, CLIENTCONNECTWAIT, SDADDRESSES,
               SDPORT, MAXIMUMCONCURRENTJOBS, HEARTBEATINTERVAL]
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import Suppress, Regex, quotedString, restOfLine, Keyword, nestedExpr, Group, OneOrMore, Word, Literal, alphanums, removeQuotes, replaceWith, nums, printables
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def _handle_ip(*x):
            a,b,c =  x[2]
            return '  %s = { %s }' % (a,c[0])

        def _handle_addr(*x):
            a,b,c =  x[2]
            self._set(SDADDRESSES, '  %s' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np(PList('sd port'), gr_number, action=self._parse_setter(SDPORT))
        gr_line = gr_line | np((ADDRESS,'sd address', SDADDRESS), action=self._parse_setter(ADDRESS))
        gr_line = gr_line | np((PASSWORD,), action=lambda x: x)
        gr_line = gr_line | np((DEVICE,), action=self._parse_setter(DEVICE))
        gr_line = gr_line | np(PList('media type'), action=self._parse_setter(MEDIATYPE))
        gr_line = gr_line | np(PList('auto changer'), gr_yn, action=self._parse_setter(AUTOCHANGER))
        gr_line = gr_line | np(PList('maximum concurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
        gr_line = gr_line | np(PList('allow compression'), gr_yn, action=self._parse_setter(ALLOWCOMPRESSION))
        gr_line = gr_line | np(PList('heartbeat interval'), action=self._parse_setter(HEARTBEATINTERVAL))

        gr_line = gr_line | np(PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
        gr_line = gr_line | np(PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
        gr_line = gr_line | np(PList('client connect wait'), action=self._parse_setter(CLIENTCONNECTWAIT))

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(PList('sd addresses'), nestedExpr('{','}', OneOrMore(da_ip)), _handle_addr)


        gr_res = OneOrMore(gr_line)
        result = gr_res.parseString(string, parseAll=True)
        return 'Storage: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''String representation of a Storage suitable for inclusion in a Director configuration.'''
        self.output = ['Storage {\n  Name = "%(name)s"' % self,'}']
        if self.director_id:
            a = StoragePasswordStore(self[ID], self.director_id)
            if getattr(a,PASSWORD,None): self.output.insert(-1,'  Password = "%s"' % a.password)
        
        for key in self.dir_keys: self._simple_phrase(key)
        for key in self.BOOL_KEYS: self._simple_phrase(key)
        return '\n'.join(self.output)

# }}}
    # {{{ sd(): 

    def sd(self):
        '''String representation of a Storage suitable for inclusion in a Storage configuration.'''
        self.output = ['Storage {\n  Name = "%(name)s"' % self,'}']
        for key in self.sd_keys: self._simple_phrase(key)
        # Special keys
        if self[ADDRESS]: self.output.insert(-1,'%sSDAddress = %s' % (self.prefix, '"' + self[ADDRESS] + '"'))
        return '\n'.join(self.output)

# }}}
    # {{{ _cli_special_setup(): add password support

    def _cli_special_setup(self):
        '''Add CLI switches for password handling.'''
        self._cli_parser_group(
            [PASSWORD, (DIRECTOR,None,'Director (name or ID) to associate with a password')],
            "Password set/change",
            "Passwords are associated with directors, so changing a password requires "
            "that you specify the director to which that password applies.  Set the password to "
            "a value of 'generate' to auto-generate a password."
            )
        return

    # }}}
    # {{{ _cli_special_do_parse(args): add password support

    def _cli_special_do_parse(self, args):
        '''Handle CLI switches for password management.'''
        if (args.password == None) and (args.director == None): return # Nothing to do!
        if (args.password == None) ^ (args.director == None):
            print('\n***WARNING***: You must specify both a password and a director to change a password.  Password not changed.\n')
            return              # Bail on any password changes, but otherwise continue
        d = bacula_tools.Director()
        try: d.search(args.director)
        except: d.search(args.director)
        if not d[ID]:
            print('\n***WARNING***: Unable to find a director using "%s".  Password not changed\n' % args.director)
            return
        password = StoragePasswordStore(self[ID], d[ID])
        password.password = args.password
        password.store()
        return

    # }}}
    # {{{ _cli_special_print(): add password support

    def _cli_special_print(self):
        '''Print out the passwords for the CLI.'''
        print('\nPasswords:')
        sql = 'select director_id from %s where %s = %%s' % (StoragePasswordStore.table, StoragePasswordStore.column1)
        for row in self.bc.do_sql(sql, self[ID]):
            password = StoragePasswordStore(self[ID], row[0])
            d = bacula_tools.Director().search(row[0])
            print('%30s: %s' % (d[NAME], password.password))
        return

    # }}}
    # {{{ _cli_special_clone(oid):

    def _cli_special_clone(self, oid):
        '''Storage clones should have the same sets of passwords as the source object.'''
        select = 'SELECT %s, director_id, password FROM storage_pwords WHERE storage_id = %%s' % self[ID]
        insert = 'INSERT INTO storage_pwords (storage_id, director_id, password) VALUES (%s,%s,%s)'
        for row in self.bc.do_sql(select, oid): self.bc.do_sql(insert, row)
        return

# }}}

def main():
    s = Storage()
    s.cli()

if __name__ == "__main__": main()

