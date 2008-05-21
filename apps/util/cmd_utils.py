import readline, sys
from cmd import Cmd

class DefaultShell(Cmd):
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
