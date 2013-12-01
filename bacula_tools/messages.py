#! /usr/bin/env python

from __future__ import print_function
try: from . import *
except: from bacula_tools import *

class Messages(DbDict):
    SETUP_KEYS = [(DATA, ''),]
    table = MESSAGES
    _select = 'SELECT ref_id, link_type FROM messages_link WHERE messages_id=%s'
    _insert = 'INSERT INTO messages_link (messages_id, ref_id, link_type) VALUES (%s, %s, %s)'
    _delete = 'DELETE FROM messages_link WHERE messages_id = %s AND ref_id=%s AND link_type=%s'
    # {{{ parse_string(string, obj=None):

    def parse_string(self, string, obj=None):
        '''Extend the standard parse_string functionality with object linkage.
        This is the solution I came up with for associating a Message with
        a Director, Client, or Storage object.
        '''
        retval = DbDict.parse_string(self, string)
        if obj: self.link(obj)
        return retval

        # }}}
    # {{{ link(obj):

    def link(self, obj):
        '''If I were willing to really wed this to MySQL, I should switch to REPLACE INTO.
        Since I'm not, we'll just do an insert and check for a duplication error.'''
        try:
            self.bc.do_sql(self._insert, (self[ID], obj[ID], obj.IDTAG))
        except Exception as e:
            if e.args[0] == 1062: pass # 1062 is what happens when you try to insert a duplicate row
            else:
                print(e)
                raise

                # }}}
    # {{{ unlink(obj): unlink the device from a storage daemon

    def unlink(self, obj):
        '''Remove the link between this Message and the given object.'''
        self.bc.do_sql(self._delete, (self[ID], obj[ID], obj.IDTAG))
        return

            # }}}
    # {{{ __str__(): 

    def __str__(self):
        '''String representation suitable for inclustion in any config file.'''
        output = 'Messages {\n  Name = "%(name)s"\n  %(data)s\n}' % self
        return output

# }}}
    # {{{ _cli_special_setup(): add in linkage support

    def _cli_special_setup(self):
        '''Add CLI switches to link objects to this.  The object-type is required
        as you could easily have the same name for Directors, Clients, and
        Storage.
        '''
        group = optparse.OptionGroup(self.parser, "Object links",
                                     "Messages are used by clients, storage daemons, and directors.")
        group.add_option('--add-link', metavar='STORAGE_DAEMON')
        group.add_option('--remove-link', metavar='STORAGE_DAEMON')
        group.add_option('--object-type', help='Optional device type to disambiguate the desired linkage')
        self.parser.add_option_group(group)
        return

    # }}}
    # {{{ _cli_special_do_parse(args): handle password parsing

    def _cli_special_do_parse(self, args):
        '''Handle the CLI switches for linkage.  Use the object type to provide a context
        for name lookup.'''
        obj = None
        if args.object_type: obj = getattr(bacula_tools, args.object_type.capitalize(), None)
            
        if args.add_link:
            if obj: target = obj().search(args.add_link)
            else:
                for key in [Client, Storage, Director]:
                    target = key().search(args.add_link)
                    if target[ID]: break
            if target[ID]: self.link(target)
            else: print('Unable to find anything named', args.add_link)

        if args.remove_link:
            if obj: target = obj().search(args.remove_link)
            else:
                for key in [Client, Storage, Director]:
                    target = key().search(args.remove_link)
                    if target[ID]: break
            if not target: print('Unable to find anything named', args.remove_link)
            else: self.unlink(target)

        return

# }}}
    # {{{ _cli_special_print(): print out passwords

    def _cli_special_print(self):
        '''Print out the linked objects.'''
        resultset = self.bc.do_sql(self._select, self[ID])
        if not resultset: return
        fmt = '%'+ str(self._maxlen) + 's'
        for row in resultset:
            for key in [Client, Storage, Director]:
                if key.IDTAG == row[1]: print(fmt % key().search(row[0])[NAME])
        return

    # }}}

def main():
    s = Messages()
    s.cli()

if __name__ == "__main__": main()

