import readline, sys
from cmd import Cmd

class DefaultShell(Cmd):
    '''A Cmd shell with some useful defaults (empty line does not repeat command, etc).'''
    def __init__(self):
        Cmd.__init__(self)
        self.prompt = "> "
    
    def do_hist(self, args):
        print self._hist
        
    def do_exit(self, args):
        sys.exit(0)
        
    def do_EOF(self, args):
        print
        self.do_exit(args)
    
    def do_help(self, args):
        Cmd.do_help(self, args)
        
    def preloop(self):
        Cmd.preloop(self)
        
        self._hist = []
        self._locals = {}
        self._globals = {}
        
    def postloop(self):
        Cmd.postloop(self)
        
    def emptyline(self): pass

import os, atexit
class HistorySavingDefaultShell(DefaultShell):
    DefaultHistoryLocation = os.path.join(os.environ['HOME'], '.munge_history')
        
    def __init__(self, history_file=DefaultHistoryLocation, clear_history=False):
        DefaultShell.__init__(self)
        
        if clear_history:
            try:
                os.remove(history_file)
            except IOError: pass

        try:
            readline.read_history_file(history_file)
        except IOError: pass
        
        atexit.register(readline.write_history_file, history_file)
        