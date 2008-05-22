import glob, readline, re, sys

from munge.proc.trace_core import TraceCore
from apps.util.cmd_utils import DefaultShell
from munge.util.iter_utils import flatten
from munge.util.err_utils import warn, info

BuiltInPackages = ['munge.proc.builtins', 'munge.proc.modes.split', 'munge.proc.modes.anno', 'apps.comma']

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
    def __init__(self):
        DefaultShell.__init__(self)
        self.tracer = TraceCore(libraries=BuiltInPackages)
        self.prompt = "trace> "
        
        self.files = []
        
        self.last_exception = None
        self.output_file = None
        
    def preloop(self):
        '''Executed before the command loop is entered.'''
        DefaultShell.preloop(self)
        # remove '-' (for option completion) and a number of shell separators (for path completion)
        # from the set of completer delimiters
        readline.set_completer_delims(re.sub(r'[-/*~\\]', '', readline.get_completer_delims()))
        
    def precmd(self, line):
        '''Executed before every command is interpreted.'''
        cleaned_line = line.strip()
        
        self._hist.append(cleaned_line)
        return cleaned_line
        
    def do_load(self, args):
        '''Handles the _load_ command (loads a filter).'''
        modules = args.split()
        
        old_modules = set(self.tracer.available_filters_dict.keys())
        self.tracer.add_modules(modules)
        modules = set(self.tracer.available_filters_dict.keys())
        
        added_modules = modules.difference(old_modules)
        if added_modules:
            info("%s modules added:", len(added_modules))
            for module in added_modules: 
                info("\t%s", module)
        else:
            info("No modules added.")
        
    def do_list(self, args):
        '''Handles the _list_ command (lists loaded filters).'''
        self.tracer.list_filters()
        
    def do_with(self, args):
        '''Handles the _with_ command (specifies filter input).'''
        args = args.split()
        if args:
            self.files = list(flatten(glob.glob(arg) for arg in args))
            
        info("Working set is: " + list_preview(self.files))

    def get_filter_by_switch(self, switch_name):
        is_option_long_name = switch_name.startswith('--')

        for filter in self.tracer.available_filters_dict.values():
            if is_option_long_name:
                if filter.long_opt == switch_name[2:]:
                    return filter.__name__
            else:
                if filter.opt == switch_name[1:]:
                    return filter.__name__

        warn("No filter with switch %s found.", switch_name)
        return None
        
    def do_run(self, args):
        '''Handles the _run_ command (processes a filter).'''
        args = args.split()
        
        if not args: return

        filter_name = args.pop(0)
        if filter_name.startswith('--'): # a long option name was given
            filter_name = self.get_filter_by_switch(filter_name)
        elif filter_name.startswith('-'): # a short option name was given
            filter_name = self.get_filter_by_switch(filter_name)
        if not filter_name: # no filter with the requested switch was found
            return

        if args:
            filter_args = args
        else:
            filter_args = None
            
        try:
            old_stdout = sys.stdout
            
            if self.output_file:
                sys.stdout = open(self.output_file, 'w')
                
            self.tracer.run( [(filter_name, filter_args)], self.files )
            print
        except KeyboardInterrupt:
            info("\nFilter run %s halted by user.", filter_run_name(filter_name, filter_args))
        except Exception, e:
            info("Filter run %s halted by framework:", filter_run_name(filter_name, filter_args))
            info("\t%s (%s)", e.message, e.__class__.__name__)
            
            self.last_exception = sys.exc_info()
        finally:
            sys.stdout = old_stdout
            
    def do_bt(self, args):
        self.do_backtrace(args)
        
    def do_backtrace(self, args):
        if self.last_exception:
            sys.excepthook(*self.last_exception)
            
    def do_into(self, args):
        def print_output_destination():
            if self.output_file is None:
                print "Filter output will be sent to the console."
            else:
                print "Filter output will be redirected to: %s" % self.output_file
                
        args = args.split(' ', 1)
        output_file = args[0]
        
        if output_file:
            if output_file == 'stdout':
                self.output_file = None
            else:
                self.output_file = output_file
                
        print_output_destination() # report on output destination in any case

    def default(self, args):
        self.do_run(args)

    def completedefault(self, *args):
        return self.complete_run(*args)

    def get_filter_attributes(self, attr):
        return [getattr(filter, attr) for filter in self.tracer.available_filters_dict.values()]
            
    def get_long_forms(self):
        return ["--" + long_opt for long_opt in self.get_filter_attributes('long_opt')]
        
    def get_short_forms(self):
        return ["-" + opt for opt in self.get_filter_attributes('opt')]
        
    def complete_run(self, text, line, begin_index, end_index):
        '''Returns completions for the _run_ command: either a long option name, a short one, or a filter name.'''
        # Be careful with the cmd module; it seems to swallow all getattr exceptions silently (eg accessing 
        # a non-existent member of this class succeeds)
        if text.startswith('--'):
            return [opt for opt in self.get_long_forms() if opt.startswith(text)]
        elif text.startswith('-'):
            return [opt for opt in self.get_short_forms() if opt.startswith(text)]
        else: # completing a filter name or a filter argument
            # Case insensitive comparison here
            filter_names = [name for name in self.tracer.available_filters_dict.keys() if name.lower().startswith(text.lower())]
            return filter_names
            
    def complete_with(self, text, line, begin_index, end_index):
        '''Returns completions for the _with_ command: paths of which the given text is a prefix.'''
        # TODO: make optionally case-insensitive. Is there a better way short of giving a glob [Ll][Ii][Kk][Ee] this?
        return self.filename_complete(text)
        
    def complete_load(self, text, line, begin_index, end_index):
        '''Returns completions for the _load_ command: all modules available to Python.'''
        return self.filename_complete(text)
        
    def filename_complete(self, text):
        return [path for path in glob.glob(text + '*') if path.startswith(text)]
        
if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass

    sh = Shell()
    sh.cmdloop()
