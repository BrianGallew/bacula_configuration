from __future__ import print_function
import re
from . import *
import bacula_tools

class StringParseSupport:
    '''parse a string out into top-level resource items and pass them off to the relevant classes.'''
    RB = '}'
    LB = '{'
    file_re = re.compile(r'\s@(.*)\s+', re.MULTILINE)
    comment_re = re.compile(r'#.*', re.MULTILINE)
    semicolon_re = re.compile(r';', re.MULTILINE)
    blankline_re = re.compile(r'^\s+$', re.MULTILINE)
    def __init__(self, output):
        self.output = output
        self.parse_queue = {}
        self.parsed = []
        self.director_config = False
        self.sd_config = False
        self.fd_config = False
        return

    def file_replacement(self, string):
        ''' Do a quick pass through the string looking for file imports.  If/When
        you find any, replace the file import statement with the contents of
        the file to be imported.  Repeat until there are no more file import statements.'''

        # Strip the comments and blank lines out
        string = self.blankline_re.sub('', self.comment_re.sub('', string))

        # Search for any file import statements
        groups = self.file_re.search(string)

        while groups:           # Iterate through the file imports
            filename = groups.group(1)
            string_without_comments = self.comment_re.sub('', open(filename).read())
            string = string.replace(groups.group(), string_without_comments)
            # re-strip blank lines *after* doing the insert.
            string = self.blankline_re.sub('', string)
            # Look again for import statements
            groups = self.file_re.search(string)
        return string

    def break_into_stanzas(self, string):
        parts = string.split(self.RB)

        # Split it up into parts, stored in self.parse_queue
        while parts:
            current = parts.pop(0)
            while current.count(self.RB) < (current.count(self.LB) - 1): current += self.RB + parts.pop(0)
            try: name, body = current.split(self.LB,1)
            except:
                self.output(current)
                raise
            name = name.strip().lower()
            self.parse_queue.setdefault(name, []).append(body.strip())
            while parts and parts[0] == '\n': del parts[0]
        return

    def analyze_queue(self):
        # Determine what kind of config this is.
        if CATALOG.lower() in self.parse_queue: self.director_config = True
        elif DEVICE in self.parse_queue: self.sd_config = True
        else: self.fd_config = True
        return

    def parse_one_stanza_type(self, key):
        if not key in self.parse_queue: return
        # Actually parse something
        for body in self.parse_queue[key]:
            try:
                obj = bacula_tools._DISPATCHER[key]()
                self.parsed.append(obj)
                if key == DIRECTOR: result = obj.parse_string(body, self.director_config, self.parsed[0])
                elif key == CATALOG.lower(): result = obj.parse_string(body, self.parsed[0])
                else: result = obj.parse_string(body)
                self.output(result)
            except Exception as e:
                msg = '%s: Unable to handle %s at this time:\n%s' % (key.capitalize(), e,body.strip())
                self.output(msg)
        del self.parse_queue[key]
        return

    def parse_it_all(self, string):
        string = self.file_replacement(string)

        # It should be observed that this statement causes scripts with
        # embedded semi-colons to break parsing.
        string = self.semicolon_re.sub('\n',  string).replace('\\\n','').replace('\n\n', '\n')

        # Fills in self.parse_queue
        self.break_into_stanzas(string)
        self.analyze_queue()

        # Actually parse the various parts
        # it turns out to be important to do these in a specific order.
        if self.sd_config: self.parse_one_stanza_type(STORAGE)
        if self.fd_config: self.parse_one_stanza_type(CLIENT)
        if self.fd_config: self.parse_one_stanza_type(FILEDAEMON)
        if self.director_config:self.parse_one_stanza_type(DIRECTOR)
        for name in self.parse_queue.keys(): self.parse_one_stanza_type(name)

        return self.parsed
    

def setup_for_parsing():
    pass

def parser(string, output=print):
    setup_for_parsing()
    p = StringParseSupport(output)
    return p.parse_it_all(string)

def parser_old(string, output=print):
    '''parse a string out into top-level resource items and pass them off to the relevant classes.'''
    # strip out comments, and turn semi-colons into newlines
    # NB: if you have embedded semi-colons in any values (e.g. runscripts),
    # You will lose here.
    RB = '}'
    LB = '{'
    file_re = re.compile(r'\s@(.*)\s+', re.MULTILINE)
    comment_re = re.compile(r'#.*', re.MULTILINE)
    semicolon_re = re.compile(r';', re.MULTILINE)
    blankline_re = re.compile(r'^\s+$', re.MULTILINE)
    # Strip the comments  and blank lines out
    string = blankline_re.sub('', comment_re.sub('', string))

    # Do a quick pass through the string looking for file imports.  If/When
    # you find any, replace the file import statement with the contents of
    # the file to be imported.  Repeat until there are no more file import statements.
    groups = file_re.search(string)
    while groups:
        filename = groups.group(1)
        string = blankline_re.sub('', string.replace(groups.group(), comment_re.sub('', open(filename).read())))
        groups = file_re.search(string)

    # It should be observed that this statement causes scripts with
    # embedded semi-colons to break parsing.
    string = semicolon_re.sub('\n',  string).replace('\\\n','').replace('\n\n', '\n')
    
    parts = string.split(RB)
    parse_queue = {}
    parsed = []

    # Split it up into parts, stored in parse_queue
    while parts:
        current = parts.pop(0)
        while current.count(RB) < (current.count(LB) - 1): current += RB + parts.pop(0)
        try: name, body = current.split(LB,1)
        except:
            output(current)
            raise
        name = name.strip().lower()
        parse_queue.setdefault(name, []).append(body.strip())
        while parts and parts[0] == '\n': del parts[0]

    # Determine what kind of config this is.
    director_config = False
    sd_config = False
    fd_config = False
    if CATALOG.lower() in parse_queue: director_config = True
    elif DEVICE in parse_queue: sd_config = True
    else: fd_config = True

    # Actually parse the various parts
    for name in parse_queue.keys():
        for body in parse_queue[name]:
            try:
                obj = bacula_tools._DISPATCHER[name]()
                parsed.append(obj)
                if name == DIRECTOR: result = obj.parse_string(body, director_config)
                else: result = obj.parse_string(body)
                output(result)
            except Exception as e:
                msg = '%s: Unable to handle %s at this time:\n%s' % (name.capitalize(), e,body.strip())
                output(msg)
    if director_config:
        this_director = [x for x in parsed if type(x) == Director][0]
        for x in parsed:
            if type(x) == Catalog: x._set(DIRECTOR_ID, this_director[ID])
    return parsed
