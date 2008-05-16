from optparse import OptionParser, OptionGroup
from itertools import izip, count
import sys, os, re
from sets import Set

from munge.io.guess import GuessReader
from munge.trees.traverse import leaves
from munge.cats.paths import applications_per_slash
from munge.util.err_utils import warn, info
from munge.proc.dynload import (get_available_filters_dict, 
                                load_requested_packages, 
                                get_argcount_for_method)

BuiltInPackages = ['munge.proc.builtins', 'munge.proc.modes.split', 'munge.proc.modes.anno']

class Filter(object):
    '''Every filter extends this class, which defines `don't care' implementations of the four hook
    functions. For each Derivation object (a bundle of the derivation object itself and some metadata),
    the framework calls each of the below methods.'''
    
    def accept_comb_and_slash_index(self, leaf, comb, slash_index, info=None):
        '''This is invoked by the framework for every slash of every category at a derivation leaf.'''
        pass
    def accept_leaf(self, leaf): 
        '''This is invoked by the framework for every derivation leaf.'''
        pass
    def accept_derivation(self, deriv): 
        '''This is invoked by the framework for each Derivation object.'''
        pass
    def output(self): 
        '''This is invoked by the framework after each derivation has been processed.'''
        pass

    # Concrete filters should define a long name ('--long-name') for command-line invocation.
    long_opt = "??"
    # Concrete filters should define a short name ('-l') for command-line invocation.
    opt = "?"
    
    # This is displayed after the long name as an intuitive name for any arguments the filter may expect.
    arg_names = ''
    
def run_builtin_filter(option, opt_string, value, parser, *args, **kwargs):
    filter_class_name = args[0]
    
    # optparse will return either a single value, or a tuple of values.
    # We wrap a single argument in a tuple for consistency
    if (value is not None) and not isinstance(value, (list, tuple)):
        value = (value, )
        
    parser.values.filters_to_run.append( (filter_class_name, value) )
    
def add_filter_to_optparser(parser, filter):
    '''Given a filter, this registers it with the option parser, allowing it to be selected on the
command line.'''
    argcount = get_argcount_for_method(filter.__init__)
    
    opt_dict = {
        'help': filter.__doc__,     # Help string is the filter docstring
        'dest': filter.long_opt,    # Destination variable is the same as the long option name
        'metavar': filter.arg_names,# Metavar names are supplied by the filter
        'action': 'callback',
        'callback': run_builtin_filter,
        'callback_args': (filter.__name__, ) # Pass in the filter's class name
    }
    
    # If the filter expects arguments, set the correct number of arguments and assume that it takes
    # string arguments (for consistency).
    if argcount > 0:
        opt_dict['nargs'] = argcount
        opt_dict['type'] = 'string'
    
    parser.add_option("-" + filter.opt, "--" + filter.long_opt, **opt_dict)
    
def list_filters(modules_loaded, filters):
    '''Prints a list of all the filters loaded, with a summary of the number and role of the arguments
each filter takes.'''
    print "%d packages loaded (%s), %d filters available:" % (len(modules_loaded), 
                                                              ", ".join(mod.__name__ for mod in modules_loaded),
                                                              len(filters))
    for (filter_name, filter) in sorted(filters.iteritems(), key=lambda (name, filter): name):
        print "\t%s\n\t\t(%d args, -%s, --%s%s)" % (filter_name, 
                                             get_argcount_for_method(filter.__init__), 
                                             filter.opt, 
                                             filter.long_opt,
                                             (' '+filter.arg_names) if filter.arg_names else '')
        
# Adapted from Python Library Reference
def register_filter(option, opt_string, value, parser, *args, **kwargs):
    '''The user is able to specify filters by name using the '-r' switch in this way:
    -r FilterName1 arg1 arg2 -r FilterName2 arg1
This requires us to handle consumption of arguments because we cannot tell at the time
we encounter the filter name how many arguments it expects.
This callback is invoked by optparse upon encountering a '-r' switch; it consumes all
arguments until another switch is encountered, registering them as arguments to be passed
to the filter when it is invoked.'''
    filter_name = value
    filter_args = []
    
    rargs = parser.rargs # remaining optparse arguments
    while rargs:
        arg = rargs[0]
        
        if ((arg[:2] == '--' and len(arg) > 2) or
            (arg[:1] == '-' and len(arg) > 1 and arg[1] != '-')):
            break
        else:
            filter_args.append( arg )
            del rargs[0]
            
    parser.values.filters_to_run.append( (filter_name, filter_args) )
    
def register_builtin_switches(parser):
    '''Registers the command-line switches which are always available as an option group.'''
    group = OptionGroup(parser, title='Built-in operations')

    group.add_option("-l", "--load-package", help="Makes available all filters from the given package.",
                      action='append', dest='packages', metavar="PKG")
    group.add_option("-L", "--list-filters", help="Lists all loaded filters.",
                      action='store_true', dest='do_list_filters')
    group.add_option("-r", "--run", help="Runs a filter.", type='string', nargs=1,
                      action='callback', callback=register_filter)
                      
    group.add_option("-0", "--end", help="Dummy option to separate -r arguments from input arguments.", 
                      action='store_true')
    
    group.add_option("-q", "--quiet", help="Suppress diagnostic messages.", 
                      action='store_false', dest='verbose')
    group.add_option("-v", "--verbose", help="Print diagnostic messages.", 
                      action='store_true', dest='verbose')

    parser.add_option_group(group)

def filter_library_switches(argv):
    '''This strips argv of all command-line switches of the form -lPACKAGE where PACKAGE is a 
Python package exposing Filter subclasses, returning a pair (list of PACKAGE names, stripped argv).'''
    new_argv = []
    library_names = []

    for arg in argv:
        matches = re.match(r'-l(.+)', arg)
        if matches:
            library_names.append(matches.group(1))
        else:
            new_argv.append(arg)

    return new_argv, library_names

def main(argv):
    parser = OptionParser(conflict_handler='resolve') # Intelligently resolve switch collisions
    parser.set_defaults(verbose=True, filters_to_run=[], packages=BuiltInPackages)
    
    # If any library loading switches (-l) are given, collect their names and remove them from argv
    argv, user_defined_libraries = filter_library_switches(argv)
    
    # Load built-in filters (those under BuiltInPackages)
    loaded_modules = set(load_requested_packages(BuiltInPackages))
    # Load user-requested filters (passed by -l on the command line)
    loaded_modules.update(load_requested_packages(user_defined_libraries))
    # Build dictionary mapping filter names to filter classes
    available_filters_dict = get_available_filters_dict(loaded_modules)

    # For each available filter, allow it to be invoked with switches on the command line
    for filter in available_filters_dict.values(): add_filter_to_optparser(parser, filter)
    
    # Load built-in optparse switches
    register_builtin_switches(parser)
    
    # Perform option parse, check for user-requested filter classes
    opts, remaining_args = parser.parse_args(argv)
    # Done with parser
    parser.destroy()
    
    # Take remaining arguments as input file names
    files = remaining_args[1:] # remaining_args[0] seems to be sys.argv[0]
    
    # If switch -L was passed, dump out all available filter names and quit
    if opts.do_list_filters:
        list_filters(loaded_modules, available_filters_dict)
        sys.exit(0)

    # Run requested filters
    filters = []
    
    filters_to_run = opts.filters_to_run
    for filter_name, args in filters_to_run:
        # For a no-args switch, optparse passes in None; we substitute an empty tuple for
        # consistency
        if not args: args = ()
        
        try:
            filter_class = available_filters_dict[filter_name]
            filters.append(filter_class(*args))
        except KeyError:
            warn("No filter with name `%s' found.", filter_name)
    
    for file in files:
        if opts.verbose: info("Processing %s...", file)
        for derivation_bundle in GuessReader(file):
            for leaf in leaves(derivation_bundle.derivation):
                for filter in filters:
                    filter.accept_leaf(leaf)

                    try:
                        for comb, slash_index in izip(applications_per_slash(leaf), count()):
                            filter.accept_comb_and_slash_index(leaf, comb, slash_index)
                    except AttributeError: # TODO: hacky and inefficient, need this to work for PTB too
                        pass

            for filter in filters:
                filter.accept_derivation(derivation_bundle)
    
    for filter in filters:
        filter.output()
    
if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass

    main(sys.argv)
