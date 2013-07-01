'''Bacula configuration database stuff: common routines, credentials, etc'''
# Bacula_Config and BSock classes and various definitions used by Bacula python programs.

import os, sys, socket, hmac, base64, hashlib, re, time
from random import randint
from struct import pack, unpack

from .. import *
        
class BSock:
    '''Sometimes, you want to talk to various Bacula daemons without the
    overhead of firing up bconsole, particularly since that will involve
    shell interaction as well fun parsing foo.  This can make it a bit
    easier.
    '''
# {{{ __init__(address, password, myname, port, debug=False, timeout=5):
    def __init__(self, address, password, myname, port, debug=False, timeout=5):
        self.debug = debug
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(timeout) # Don't take forever trying to do stuff
        self.log('connecting to: %s' % str((address,port)))
        self.connection.connect((address,port))
        self.password = password
        self.name = myname
        return
# }}}
# {{{ log(msg): Debugging output

    def log(self, msg):
        if self.debug:
            sys.stderr.write(msg)
            sys.stderr.flush()
        return

    # }}}
# {{{ auth(): authenticate a new connection

    def auth(self):
        '''The bulk of this was written by Matthew Ife, so thanks!'''
        
        self.send("Hello %s calling\n" % (self.name,)) # this is effectively our username
        challenge = self.recv() # Receive the challenge response
        m = re.search("auth cram-md5 (<.+?>)", challenge) # parse the challenge out of the returned string
        chal = m.group(1)
        
        pw = hashlib.md5(self.password).hexdigest()
        self.send(base64.b64encode(hmac.new(pw, chal).digest())[:-2]) # hmac and base64 encode the request

        result = self.recv() # receive response
        if result != "1000 OK auth\n": raise ValueError("Authentication Failed %s" % (result,))# failed

        # send our challenge response
        self.send("auth cram-md5 <%d.%d@%s> ssl=0\n" % (randint(1,99999999), int(time.time()), self.name))
        self.recv()                 # get the response back
        self.send("1000 OK auth\n") # Dont even check the response here!

        # This is basically cheating the protocol spec! :-)
        data = self.recv()
        if not re.match(".* OK.*",data): # auth complete
            raise ValueError("Unexpected packet received %s" % (data,))
        self.auth = True
        return data

    # }}}
# {{{ send(message): send a message to the remote daemon

    def send(self, message):
        ldata = pack('!i',len(message))
        self.connection.send(ldata)
        self.log( 'sending:  (%d) %s\n' % (len(message), message))
        self.connection.send(message)
        return

    # }}}
# {{{ recv(): Get a one line response from the remote daemon

    def recv(self):
        msglen = unpack('!i', self.connection.recv(4))[0]
        if msglen < 0: return ''
        response = self.connection.recv(msglen)
        self.log( 'received: %s' % response)
        return response

    # }}}
# {{{ recv_all(): receive a multi-line response from the remote daemon

    def recv_all(self):
        """Gets all lines of a request"""
        r = ""
        s = self.recv()
        while s:
            r += s
            s = self.recv()
        return r

    # }}}
# {{{ version(): request version info from the remote daemon (useless?)

    def version(self):
        self.send('version')
        return self.recv()

    # }}}
# {{{ status(args=''): request status of the remote daemon

    def status(self, args=''):
        if args: self.send('.status %s' % args)
        else: self.send('status')
        return self.recv_all()

    # }}}
# {{{ _time(): format the time for uniqueifying various things

    def _time(self):
        return time.strftime('%F_%H.%M.%S_00')

    # }}}
