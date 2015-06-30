#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import bacula_tools
import optparse


class Messages(bacula_tools.DbDict):
    SETUP_KEYS = [(bacula_tools.DATA, ''), ]
    table = bacula_tools.MESSAGES
    _select = 'SELECT ref_id, link_type FROM messages_link WHERE messages_id=%s'
    _insert = 'INSERT INTO messages_link (messages_id, ref_id, link_type) VALUES (%s, %s, %s)'
    _delete = 'DELETE FROM messages_link WHERE messages_id = %s AND ref_id=%s AND link_type=%s'

    def link(self, obj):
        '''If I were willing to really wed this to MySQL, I should switch to REPLACE INTO.
        Since I'm not, we'll just do an insert and check for a duplication error.'''
        try:
            self.bc.do_sql(
                self._insert, (self[bacula_tools.ID], obj[bacula_tools.ID], obj.IDTAG))
        except Exception as e:
            if e.args[0] == 1062:
                # 1062 is what happens when you try to insert a duplicate row
                pass
            else:
                print(e)
                raise

    def unlink(self, obj):
        '''Remove the link between this Message and the given object.'''
        self.bc.do_sql(
            self._delete, (self[bacula_tools.ID], obj[bacula_tools.ID], obj.IDTAG))
        return

    def __str__(self):
        '''String representation suitable for inclustion in any config file.'''
        output = 'Messages {\n  Name = "%(name)s"\n  %(data)s\n}' % self
        return output

    def _cli_special_setup(self):
        '''Add CLI switches to link objects to this.  The object-type is required
        as you could easily have the same name for Directors, Clients, and
        Storage.
        '''
        group = optparse.OptionGroup(self.parser, "Object links",
                                     "Messages are used by clients, storage daemons, and directors.")
        group.add_option('--add-link', metavar='STORAGE_DAEMON')
        group.add_option('--remove-link', metavar='STORAGE_DAEMON')
        group.add_option(
            '--object-type', help='Optional device type to disambiguate the desired linkage')
        self.parser.add_option_group(group)
        return

    def _cli_special_do_parse(self, args):
        '''Handle the CLI switches for linkage.  Use the object type to provide a context
        for name lookup.'''
        obj = None
        if args.object_type:
            obj = getattr(bacula_tools, args.object_type.capitalize(), None)

        if args.add_link:
            if obj:
                target = obj().search(args.add_link)
            else:
                for key in [bacula_tools.Client, bacula_tools.Storage, bacula_tools.Director]:
                    target = key().search(args.add_link)
                    if target[bacula_tools.ID]:
                        break
            if target[bacula_tools.ID]:
                self.link(target)
            else:
                print('Unable to find anything named', args.add_link)

        if args.remove_link:
            if obj:
                target = obj().search(args.remove_link)
            else:
                for key in [bacula_tools.Client, bacula_tools.Storage, bacula_tools.Director]:
                    target = key().search(args.remove_link)
                    if target[bacula_tools.ID]:
                        break
            if not target:
                print('Unable to find anything named', args.remove_link)
            else:
                self.unlink(target)

        return

    def _cli_special_print(self):
        '''Print out the linked objects.'''
        resultset = self.bc.do_sql(self._select, self[bacula_tools.ID])
        if not resultset:
            return
        fmt = '%' + str(self._maxlen) + 's'
        for row in resultset:
            for key in [bacula_tools.Client, bacula_tools.Storage, bacula_tools.Director]:
                if key.IDTAG == row[1]:
                    print(fmt % key().search(row[0])[bacula_tools.NAME])
        return


def main():
    s = Messages()
    s.cli()

if __name__ == "__main__":
    main()
