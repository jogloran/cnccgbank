from optparse import OptionParser
from itertools import izip, count
import sys
import os

from sets import Set

from munge.io.guess import GuessReader
from munge.trees.traverse import leaves
from munge.cats.paths import applications_per_slash

from munge.util.err_utils import warn, info

from munge.proc.dynload import get_available_filters_dict, load_requested_packages, get_argcount_for_method

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

    long_opt = "??"
    opt = "?"
    
    arg_names = ''
    
def run_builtin_filter(option, opt_string, value, parser, *args, **kwargs):
    filter_class_name = args[0]
    
    # Wrap a single argument in a tuple for consistency
    if (value is not None) and not isinstance(value, (list, tuple)):
        value = (value, )
        
    parser.values.filters_to_run.append( (filter_class_name, value) )
    
def add_filter_to_optparser(parser, filter):
    argcount = get_argcount_for_method(filter.__init__)
    
    opt_dict = {
        'help': filter.__doc__,     # Help string is the filter docstring
        'dest': filter.long_opt,    # Destination variable is the same as the long option name
        'metavar': filter.arg_names,# Metavar names are supplied by the filter
        'action': 'callback',
        'callback': run_builtin_filter,
        'callback_args': (filter.__name__, ) # Pass in the filter's class name
    }
    
    if argcount > 0:
        opt_dict['nargs'] = argcount
        opt_dict['type'] = 'string'
    
    parser.add_option("-" + filter.opt, "--" + filter.long_opt, **opt_dict)
    
def list_filters(modules_loaded, filters):
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
    parser.add_option("-l", "--load-package", help="Makes available all filters from the given package.",
                      action='append', dest='packages', metavar="PKG")
    parser.add_option("-L", "--list-filters", help="Lists all loaded filters.",
                      action='store_true', dest='do_list_filters')
    parser.add_option("-r", "--run", help="Runs a filter.", type='string', nargs=1,
                      action='callback', callback=register_filter)
                      
    parser.add_option("-0", "--end", help="Dummy option to separate -r arguments from input arguments.", 
                      action='store_true')
    
    parser.add_option("-q", "--quiet", help="Suppress diagnostic messages.", 
                      action='store_false', dest='verbose')
    parser.add_option("-v", "--verbose", help="Print diagnostic messages.", 
                      action='store_true', dest='verbose')

def main(argv):
    parser = OptionParser(conflict_handler='resolve')
    parser.set_defaults(verbose=True, filters_to_run=[], packages=BuiltInPackages)
    
    # Load built-in filters (those under BuiltInPackages)
    loaded_modules = set(load_requested_packages(BuiltInPackages))
    available_filters_dict = get_available_filters_dict(loaded_modules)

    # Built-in filters are accessible as command line switches, and are visible in optparse help
    for filter in available_filters_dict.values(): add_filter_to_optparser(parser, filter)
    
    # Load built-in optparse switches
    register_builtin_switches(parser)
    
    # Perform option parse, check for user-requested filter classes
    opts, remaining_args = parser.parse_args(argv)
    # Done with parser
    parser.destroy()
    
    # Load user-requested filter classes
    loaded_modules.update( load_requested_packages(opts.packages) )
    available_filters_dict.update( get_available_filters_dict(loaded_modules) )
    
    # Take remaining arguments as input file names
    files = remaining_args[1:] # remaining_args[0] seems to be sys.argv[0]
    
    # If switch -L was passed, dump out all available filter names and quit
    if opts.do_list_filters:
        list_filters(loaded_modules, available_filters_dict)
        sys.exit()

    # Run requested filters
    filters = []
    
    filters_to_run = opts.filters_to_run
    for filter_name, args in filters_to_run:
        if not args: args = ()
        
        try:
            filter_class = available_filters_dict[filter_name]
            filters.append(filter_class(*args))
        except KeyError:
            warn("No filter with name `%s' found.", filter_name)
    
    for file in files:
        if opts.verbose: info("Processing %s...", file)
        for derivation_bundle in GuessReader(file):
#            if opts.verbose: print >> sys.stderr, "Processing %s..." % derivation_bundle.label()
            
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
