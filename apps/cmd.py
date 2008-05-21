from munge.proc.trace_core import TraceCore
from apps.util.cmd_utils import DefaultShell

BuiltInPackages = ['munge.proc.builtins', 'munge.proc.modes.split', 'munge.proc.modes.anno']

class Shell(DefaultShell):
    def __init__(self):
        DefaultShell.__init__(self)
        self.tracer = TraceCore(libraries=BuiltInPackages)
        self.prompt = "trace> "
        
    def precmd(self, line):
        cleaned_line = line.strip()
        
        self._hist.append(cleaned_line)
        return cleaned_line
        
    def do_load(self, args):
        modules = args.split()
        
        old_modules = set(self.tracer.available_filters_dict.keys())
        self.tracer.add_modules(modules)
        modules = set(self.tracer.available_filters_dict.keys())
        
        added_modules = modules.difference(old_modules)
        print "%s modules added:" % len(added_modules)
        for module in added_modules:
            print "\t%s" % module
        
    def do_list(self, args):
        self.tracer.list_filters()
        
    def do_run(self, args):
        pass
    
if __name__ == '__main__':
    sh = Shell()
    sh.cmdloop()