#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Client(DbDict):
    SETUP_KEYS = [
        ADDRESS, CATALOG_ID, FILERETENTION, JOBRETENTION, 
        WORKINGDIRECTORY, SDCONNECTTIMEOUT, MAXIMUMNETWORKBUFFERSIZE,
        PIDDIRECTORY, HEARTBEATINTERVAL, FDADDRESSES, FDADDRESS,
        FDSOURCEADDRESS, MAXIMUMBANDWIDTHPERJOB, PKIKEYPAIR, PKIMASTERKEY,
        NOTES,
        ]
    BOOL_KEYS = [AUTOPRUNE, PKIENCRYPTION, PKISIGNATURES]
    INT_KEYS = [(FDPORT, 9102), (MAXIMUMCONCURRENTJOBS, 1), PRIORITY]
    table = CLIENTS
    IDTAG = 2
    # {{{ parse_string(string): Entry point for a recursive descent parser

    def parse_string(self, string):
        '''Populate a new object from a string.
        
        Parsing is hard, so we're going to call out to the pyparsing
        library here.  I hope you installed it!
        '''
        from pyparsing import quotedString, restOfLine, Keyword, nestedExpr, OneOrMore, Word, Literal, removeQuotes, nums, replaceWith, printables
        gr_eq = Literal('=')
        gr_stripped_string = quotedString.copy().setParseAction( removeQuotes )
        gr_opt_quoted_string = gr_stripped_string | restOfLine
        gr_number = Word(nums)
        gr_yn = Keyword('yes', caseless=True).setParseAction(replaceWith('1')) | Keyword('no', caseless=True).setParseAction(replaceWith('0'))

        def _handle_ip(*x):
            a,b,c =  x[2]
            return '  %s = { %s }' % (a,c[0])

        def _handle_fdaddr(*x):
            a,b,c =  x[2]
            self._set(FDADDRESSES, '  %s' % '\n  '.join(c))
            return

        def np(words, fn = gr_opt_quoted_string, action=None):
            p = Keyword(words[0], caseless=True).setDebug(bacula_tools.DEBUG)
            for w in words[1:]:
                p = p | Keyword(w, caseless=True).setDebug(bacula_tools.DEBUG)
            p = p + gr_eq + fn
            p.setParseAction(action)
            return p

        gr_line = np((NAME,), action=lambda x: self._set_name(x[2]))
        gr_line = gr_line | np((ADDRESS,), action=self._parse_setter(ADDRESS))
        gr_line = gr_line | np((CATALOG,), action=self._parse_setter(CATALOG_ID, dereference=True))
        gr_line = gr_line | np((PASSWORD,), action=lambda x: x) # Discard the password here!
        gr_line = gr_line | np(PList('file retention'), action=self._parse_setter(FILERETENTION))
        gr_line = gr_line | np(PList('job retention'), action=self._parse_setter(JOBRETENTION))
        gr_line = gr_line | np((PRIORITY,), gr_number, action=self._parse_setter(PRIORITY))
        gr_line = gr_line | np(PList('working directory'), action=self._parse_setter(WORKINGDIRECTORY))
        gr_line = gr_line | np(PList('pid directory'), action=self._parse_setter(PIDDIRECTORY))
        gr_line = gr_line | np(PList('heart beat interval'), action=self._parse_setter(HEARTBEATINTERVAL))
        gr_line = gr_line | np(PList('fd address'), action=self._parse_setter(FDADDRESS))
        gr_line = gr_line | np(PList('fd source address'), action=self._parse_setter(FDSOURCEADDRESS))
        gr_line = gr_line | np(PList('pki key pair'), action=self._parse_setter(PKIKEYPAIR))
        gr_line = gr_line | np(PList('pki master key'), action=self._parse_setter(PKIMASTERKEY))
        gr_line = gr_line | np(PList('fd port'), gr_number, action=self._parse_setter(FDPORT))
        gr_line = gr_line | np(PList('auto prune'), gr_yn, action=self._parse_setter(AUTOPRUNE))
        gr_line = gr_line | np(PList('maximum concurrent jobs'), gr_number, action=self._parse_setter(MAXIMUMCONCURRENTJOBS))
        gr_line = gr_line | np(PList('pki encryption'), gr_yn, action=self._parse_setter(PKIENCRYPTION))
        gr_line = gr_line | np(PList('pki signatures'), gr_yn, action=self._parse_setter(PKISIGNATURES))

        # This is a complicated one
        da_addr = np(('Addr','Port'), Word(printables), lambda x,y,z: ' '.join(z))
        da_ip = np(('IPv4','IPv6','IP'), nestedExpr('{','}', OneOrMore(da_addr).setParseAction(lambda x,y,z: ' ; '.join(z)))).setParseAction(_handle_ip)
        da_addresses = np(('fd addresses', FDADDRESSES), nestedExpr('{','}', OneOrMore(da_ip)), _handle_fdaddr)

        gr_res = OneOrMore(gr_line|da_addresses)
        result = gr_res.parseString(string, parseAll=True)
        return 'Client: ' + self[NAME]

    # }}}
    # {{{ __str__(): 

    def __str__(self):
        self.output = ['Client {\n  Name = "%(name)s"' % self,'}']
        self.output.insert(-1, '  %s = "%s"' % (CATALOG.capitalize(), self._fk_reference(CATALOG_ID)[NAME]))
        if getattr(self,DIRECTOR_ID, None):
            a = PasswordStore(self[ID], self.director_id)
            self.output.insert(-1,'  Password = "%s"' % a.password)
        for key in [ADDRESS, FDPORT, FILERETENTION,
                    JOBRETENTION, MAXIMUMCONCURRENTJOBS,
                    MAXIMUMBANDWIDTHPERJOB, PRIORITY
                    ]:
            self._simple_phrase(key)
        self._yesno_phrase(AUTOPRUNE)
        return '\n'.join(self.output)

# }}}
    # {{{ fd(): return the string that describes the filedaemon configuration

    def fd(self):
        '''This is what we'll call to dump out the config for the file daemon'''
        self.output = ['Client {\n  Name = "%(name)s"' % self, '}']
        
        for key in [WORKINGDIRECTORY, PIDDIRECTORY, HEARTBEATINTERVAL, MAXIMUMCONCURRENTJOBS,
                    FDPORT, FDADDRESS, FDSOURCEADDRESS, SDCONNECTTIMEOUT,
                    MAXIMUMNETWORKBUFFERSIZE, MAXIMUMBANDWIDTHPERJOB, PKIKEYPAIR, PKIMASTERKEY
                    ]:
            self._simple_phrase(key)
        if self[FDADDRESSES]:
            self.output.insert(-1, '  %s {' % FDADDRESSES.capitalize())
            self.output.insert(-1,  self[FDADDRESSES])
            self.output.insert(-1, '  }')
        self._yesno_phrase(PKIENCRYPTION)
        self._yesno_phrase(PKISIGNATURES)
        return '\n'.join(self.output)

    # }}}
    # {{{ _cli_special_setup(): add in password support

    def _cli_special_setup(self):
        group = optparse.OptionGroup(self.parser,
                                     "Password set/change",
                                     "Passwords are associated with directors, so changing a password requires "
                                     "that you specify the director to which that password applies.")
        group.add_option('--password')
        group.add_option('--director')
        group.add_option('--monitor', metavar='[yes|no]')
        self.parser.add_option_group(group)
        return

    # }}}
    # {{{ _cli_special_do_parse(args): handle password parsing

    def _cli_special_do_parse(self, args):
        if (args.password == None) and (args.director == None): return # Nothing to do!
        if (args.password == None) ^ (args.director == None):
            print('\n***WARNING***: You must specify both a password and a director to change a password.  Password not changed.\n')
            return              # Bail on any password changes, but otherwise continue
        d = bacula_tools.Director()
        try: d.search(id=args.director)
        except: d.search(args.director)
        if not d[ID]:
            print('\n***WARNING***: Unable to find a director using "%s".  Password not changed\n' % args.director)
            return
        password = PasswordStore(self[ID], d[ID])
        password.password = args.password
        if args.monitor:
            if args.monitor in ['1', 'yes', 'Yes', 'YES', 'on', 'On', 'ON', 'true', 'True', 'TRUE']: password.monitor = 1
            else: password.monitor = 0
        password.store()
        return

# }}}
    # {{{ _cli_special_print(): print out passwords

    def _cli_special_print(self):
        print('\nPasswords:')
        sql = 'select director_id from %s where %s = %%s' % (PasswordStore.table, PasswordStore.column1)
        for row in self.bc.do_sql(sql, self[ID]):
            password = PasswordStore(self[ID], row[0])
            d = bacula_tools.Director().search(id=row[0])
            retval = '%30s: %s' % (d[NAME], password.password)
            if password.monitor: retval += ' (monitor)'
            print(retval)
        return

    # }}}

    def _cli_special_clone(self): pass

if __name__ == "__main__":
    s = Client()
    s.cli()
