from munge.proc.trace_core import TraceCore
from apps.util.cmd_utils import DefaultShell

BuiltInPackages = ['munge.proc.builtins', 'munge.proc.modes.split', 'munge.proc.modes.anno']

class Shell(DefaultShell):
    def __init__(self):
        DefaultShell.__init__(self)
        self.tracer = TraceCore(libraries=BuiltInPackages)
        
    def precmd(self, line):
        cleaned_line = line.strip()
        
        self._hist.append(cleaned_line)
        return cleaned_line
        
    def do_load(self, args):
        modules = args.split()
        self.tracer.add_modules(modules)
        
    def do_list(self, args):
        self.tracer.list_filters()
        
    def do_run(self, args):
        pass
    
if __name__ == '__main__':
    sh = Shell()
    sh.cmdloop()