import glob, readline, re, sys

import munge
from munge.proc.trace_core import TraceCore
from apps.util.cmd_utils import DefaultShell
from munge.util.iter_utils import flatten

BuiltInPackages = ['munge.proc.builtins', 'munge.proc.modes.split', 'munge.proc.modes.anno']

def filter_run_name(filter_name, filter_args):
    return "%s(%s)" % (filter_name, ', '.join(filter_args) if filter_args else '')
    
def list_preview(orig_l, head_elements=7, tail_elements=1):
    if not orig_l: return "{}"
    
    l = sorted(orig_l[:])
    tail = l[-tail_elements:]
    del l[-tail_elements:] # Ensure that no overlap between head and tail happens, by deleting tail first
    head = l[0:head_elements]
    
    bits = ["{ "]
    if head: 
        bits += ", ".join(head)
    if tail:
        if head:
            bits.append(", ..., ")
        bits += ", ".join(tail)
    bits.append(" }")
    
    return ''.join(bits)

class Shell(DefaultShell):
    ARG, OPT, LONG_OPT, FILTER = xrange(4)
    
    def __init__(self):
        DefaultShell.__init__(self)
        self.tracer = TraceCore(libraries=BuiltInPackages)
        self.prompt = "trace> "
        
        self.files = []
        
        self.completion_state = Shell.ARG
        
    def preloop(self):
        DefaultShell.preloop(self)
        # remove '-' and '/' from the set of completer delimiters
        readline.set_completer_delims(re.sub(r'[-/*~]', '', readline.get_completer_delims()))
        
    def precmd(self, line):
        cleaned_line = line.strip()
        
        self._hist.append(cleaned_line)
        return cleaned_line
        
    def do__reload(self, args):
        reload(munge.proc.trace_core)
        
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
        else:
            print "No modules added."
        
    def do_list(self, args):
        self.tracer.list_filters()
        
    def do_with(self, args):
        args = args.split()
        if args:
            self.files = list(flatten(glob.glob(arg) for arg in args))
            
        print "Working set is: " + list_preview(self.files)
        
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
            print "\nFilter run %s aborted." % filter_run_name(filter_name, filter_args)
            
    def get_filter_attributes(self, attr):
        return [getattr(filter, attr) for filter in self.tracer.available_filters_dict.values()]
            
    def get_long_forms(self):
        return ["--" + long_opt for long_opt in self.get_filter_attributes('long_opt')]
        
    def get_short_forms(self):
        return ["-" + opt for opt in self.get_filter_attributes('opt')]
        
    def complete_run(self, text, line, begin_index, end_index):
        # Be careful with the cmd module; it seems to swallow all getattr exceptions silently (eg accessing 
        # a non-existent member of this class succeeds)
        if text.startswith('--'):
            return filter(lambda opt: opt.startswith(text), self.get_long_forms())
        elif text.startswith('-'):
            return filter(lambda opt: opt.startswith(text), self.get_short_forms())
        else: # completing a filter name or a filter argument
            filter_names = filter(lambda name: name.startswith(text), self.tracer.available_filters_dict.keys())
            return filter_names
            
    def complete_with(self, text, line, begin_index, end_index):
        return filter(lambda path: path.startswith(text), glob.glob(text + '*'))
        
    def complete_load(self, text, line, begin_index, end_index):
        return filter(lambda pkg: pkg.startswith(text), sys.modules)
        
if __name__ == '__main__':
    sh = Shell()
    sh.cmdloop()