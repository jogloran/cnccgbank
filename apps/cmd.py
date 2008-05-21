import glob

from munge.proc.trace_core import TraceCore
from apps.util.cmd_utils import DefaultShell
from munge.util.iter_utils import flatten

BuiltInPackages = ['munge.proc.builtins', 'munge.proc.modes.split', 'munge.proc.modes.anno']

class Shell(DefaultShell):
    def __init__(self):
        DefaultShell.__init__(self)
        self.tracer = TraceCore(libraries=BuiltInPackages)
        self.prompt = "trace> "
        
        self.files = []
        
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
        if added_modules:
            print "%s modules added:" % len(added_modules)
            for module in added_modules: 
                print "\t%s" % module
        
    def do_list(self, args):
        self.tracer.list_filters()
        
    def do_with(self, args):
        args = args.split()
        self.files = list(flatten(glob.glob(arg) for arg in args))
        print "Using %s" % self.files
        
    def do_run(self, args):
        args = args.split()
        
        if len(args) == 0: return
        filter_name = args.pop(0)
        if args:
            filter_args = args
        else:
            filter_args = None
            
        try:
            self.tracer.run( [(filter_name, filter_args)], self.files )
        except KeyboardInterrupt:
            print "\nFilter run %s(%s) aborted." % (filter_name, ', '.join(filter_args) if filter_args else '')
        
    def complete_run(self, text, line, begin_index, end_index):
        pass
    
if __name__ == '__main__':
    sh = Shell()
    sh.cmdloop()