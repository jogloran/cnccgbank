import glob, readline, re, sys, os
try:
    from cmd2 import options, make_option
except ImportError:
    def options(f):
        def _f(*args, **kwargs): pass
        return _f
    def make_option(*args, **kwargs): pass
    import cmd

from munge.proc.trace_core import TraceCore
from munge.proc.dynload import get_argcount_for_method
from apps.util.cmd_utils import DefaultShell
from munge.util.iter_utils import flatten
from munge.util.err_utils import warn, info
from munge.util.list_utils import list_preview
from munge.proc.tgrep.tgrep import Tgrep

BuiltInPackages = ['munge.proc.builtins', 
                   'munge.proc.modes.split', 'munge.proc.modes.anno', 
                   'apps.comma', 'apps.comma2', 'munge.proc.tgrep.tgrep']

def filter_run_name(filter_name, filter_args):
    '''Produces a human-readable summary of a filter run: the filter name with a list of its arguments
in parentheses separated by commas.'''
    return "%s(%s)" % (filter_name, ', '.join(filter_args) if filter_args else '')

class Shell(DefaultShell):
    '''A shell interface to trace functionality.'''
    def __init__(self, files=None, verbose=True):
        DefaultShell.__init__(self)
        self.tracer = TraceCore(libraries=BuiltInPackages, verbose=verbose)
        self.prompt = "trace> "
        
        self.files = files or []
        
        self.last_exception = None
        self.output_file = None
        
        self._verbose = verbose
        
    def get_verbose(self): return self._verbose
    def set_verbose(self, is_verbose):
        self._verbose = self.tracer.verbose = is_verbose
    verbose = property(get_verbose, set_verbose)
        
    def do_quiet(self, args):
        print self._verbose
        if self._verbose: 
            self.set_verbose(False)
            info("Will generate less output.")
            
    def do_verbose(self, args):
        if not self._verbose:
            self.set_verbose(True)
            info("Will generate more output.")
        
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
        '''Loads filter modules given as package names.'''
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

    @options([ make_option('-l', '--long', action='store_true', dest='long', help='Show detailed summary', default=False),
               make_option('-s', '--sort-by', action='store', type='choice', choices=['name', 'module'], 
                           dest='sort_key', help='Display filters in a given sorted order', default='name')])
    def do_list(self, args, opts):
        """Lists all loaded filters."""
        self.tracer.list_filters(long=opts.long, filter_sort_key=opts.sort_key)
        
    def do_with(self, args):
        '''Changes or displays the working set.'''
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
        '''Runs the given filter with the given arguments on the working set.'''
        args = args.split()
        
        if not args: return

        filter_name = args.pop(0)
        if not filter_name: # no filter with the requested switch was found
            return
        if filter_name.startswith('--'): # a long option name was given
            filter_name = self.get_filter_by_switch(filter_name)
        elif filter_name.startswith('-'): # a short option name was given
            filter_name = self.get_filter_by_switch(filter_name)

        # Special case: for a one-arg filter any number of arguments are treated
        # as a single argument.
        if (filter_name in self.tracer and 
            get_argcount_for_method(self.tracer[filter_name].__init__) == 1):

            filter_args = (' '.join(args), )
        elif args is not None:
            filter_args = args
        else:
            filter_args = None
            
        def action():
            self.tracer.run( [(filter_name, filter_args)], self.files )
            print

        self.redirecting_stdout(action, filter_name, filter_args)
            
    def do_backtrace(self, args):
        '''Displays the exception backtrace for the last failed filter.'''
        if self.last_exception:
            sys.excepthook(*self.last_exception)
    do_bt = do_backtrace
            
    def do_into(self, args):
        '''Sets or displays the destination for filter output. The special filename 
'stdout' will redirect filter output to the console.'''
        def print_output_destination():
            if self.output_file is None:
                info("Filter output will be sent to the console.")
            else:
                info("Filter output will be redirected to: %s", self.output_file)
                
        args = args.split(' ', 1)
        output_file = args[0]
        
        if output_file:
            if output_file == 'stdout':
                self.output_file = None
            else:
                self.output_file = output_file
                
        print_output_destination() # report on output destination in any case

    def redirecting_stdout(self, action, filter_name, filter_args):
        try:
            old_stdout = sys.stdout
            
            if self.output_file:
                sys.stdout = open(self.output_file, 'w')
                
            action()
        except KeyboardInterrupt:
            info("\nFilter run %s halted by user.", filter_run_name(filter_name, filter_args))
        except Exception, e:
            info("Filter run %s halted by framework:", filter_run_name(filter_name, filter_args))
            info("\t%s (%s)", e.message, e.__class__.__name__)
            
            self.last_exception = sys.exc_info()
        finally:
            sys.stdout = old_stdout

    @options([ make_option('-s', '--subtree', help='Print each matching subtree only.',
                           dest='show_mode', action='store_const', const='subtree', default='subtree'),
               make_option('-w', '--whole-tree', help='Print whole tree on match (not just matching subtrees).',
                           dest='show_mode', action='store_const', const='whole_tree'),
               make_option('-l', '--label', help='Print labels of matching trees.',
                           dest='show_mode', action='store_const', const='label'),
               make_option('-t', '--tokens', help='Print tokens of matching trees.',
                           dest='show_mode', action='store_const', const='tokens'),

               make_option('-a', '--find-all', help='Find all matches (not just the first).',
                           dest='find_mode', action='store_const', const='all', default='all'),
               make_option('-1', '--find-first', help='Match only one node where possible.',
                           dest='find_mode', action='store_const', const='first') ])
    def do_tgrep(self, args, opts):
        '''Performs a tgrep query.'''
        if not args.strip(): return

        show_mode = {
            'subtree':    Tgrep.SHOW_NODE,
            'whole_tree': Tgrep.SHOW_TREE,
            'label':      Tgrep.SHOW_LABEL,
            'tokens':     Tgrep.SHOW_TOKENS
        }[opts.show_mode]
        find_mode = {
            'all':        Tgrep.FIND_ALL,
            'first':      Tgrep.FIND_FIRST
        }[opts.find_mode]

        def action():
            tgrep_filter = Tgrep(args, show_mode=show_mode, find_mode=find_mode)
            self.tracer.run_filters((tgrep_filter, ), self.files)

        self.redirecting_stdout(action, 'Tgrep', (args, ))

    do_tg = do_tgrep

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
        return [module for module in sys.modules.keys() if module.startswith(text)]
        
    def filename_complete(self, text):
        '''Returns a list of files and directories whose names are prefixes of the entered
text. Appends a directory separator to directory completions.'''
        return [path + (os.path.sep if os.path.isdir(path) else '') 
                for path in glob.glob(text + '*') 
                if path.startswith(text)]
                
def run_file(option, opt_string, value, parser, *args, **kwargs):
    '''Reads and invokes commands from a file, then terminates.'''
    script_file = value
    if not os.path.exists(script_file):
        raise RuntimeError('Script file %s not found.' % script_file)
        
    sh = Shell()
    for line in open(script_file):
        line = line.strip()
        sh.onecmd(line)
        
    sys.exit()
    
def register_builtin_switches(parser):
    parser.add_option('-F', '--file-script', help='Reads and invokes cmd.py commands from a file, then terminates. Ignores input files given on the command line.', 
                      type='string', nargs=1, action='callback', callback=run_file)
    parser.add_option('-v', '--verbose', help='Print diagnostic messages.',
                      action='store_true', dest='verbose')
    parser.add_option('-q', '--quiet', help='Make less output.',
                      action='store_false', dest='verbose')
        
from optparse import OptionParser
if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass
    
    parser = OptionParser(conflict_handler='resolve')
    parser.set_defaults(verbose=True)
    register_builtin_switches(parser)
    
    opts, remaining_args = parser.parse_args(sys.argv)
    argv = remaining_args[1:] # Take any remaining arguments as input files to start with
    
    parser.destroy()

    sh = Shell(files=argv)
    sh.cmdloop()
