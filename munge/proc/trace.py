from optparse import OptionParser
from itertools import izip, count
import sys
import os

from sets import Set

from munge.io.guess import GuessReader
from munge.trees.traverse import leaves
from munge.cats.paths import applications_per_slash
from munge.vis.dot import write_graph

from munge.util.err_utils import warn

from exceptions import NotImplementedError

from munge.proc.dynload import * # TODO: correct these
from munge.proc.builtins import *

BuiltInPackages = ['munge.proc.builtins']

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

    @property
    def long_opt(): pass
    @property
    def opt(): raise NotImplementedError, "Filters must provide at least a short name."
    
    arg_names = ()
    
def add_filter_to_optparser(parser, filter):
    argcount = get_argcount_for_method(filter.__init__)
    
    opt_dict = {
        'help': filter.__doc__,
        'dest': filter.long_opt,
        'metavar': filter.arg_names
    }
    
    if argcount > 0:
        opt_dict['action'] = 'store'
        opt_dict['nargs'] = argcount
    else:
        opt_dict['action'] = 'store_true'
    
    parser.add_option("-" + filter.opt, "--" + filter.long_opt, **opt_dict)
    
def list_filters(filters):
    for filter in filters:
        print filter
        
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

def main(argv):
    parser = OptionParser()
    
    parser.set_defaults(verbose=True, filters_to_run=[], packages=BuiltInPackages)
    
    loaded_modules = load_requested_packages(BuiltInPackages)
    available_filters_dict = get_available_filters_dict(loaded_modules)

    for filter in available_filters_dict.values(): add_filter_to_optparser(parser, filter)
    
    parser.add_option("-l", "--load-package", help="Makes available all filters from the given package.",
                      action='append', dest='packages')
    parser.add_option("-L", "--list-filters", help="Lists all loaded filters.",
                      action='store_true', dest='do_list_filters')
    parser.add_option("-r", "--run", help="Runs a filter.", type='string', nargs=1,
                      action='callback', callback=register_filter)
                      
    parser.add_option("-0", "--end", help="Dummy option to separate -r arguments from input arguments.")
    
    parser.add_option("-q", "--quiet", help="Suppress diagnostic messages.", 
                      action='store_false', dest='verbose')
    parser.add_option("-v", "--verbose", help="Print diagnostic messages.", 
                      action='store_true', dest='verbose')
    # TODO: Add option which forces the choice of a given Guesser
    
    opts, remaining_args = parser.parse_args(argv)
    
    loaded_modules.extend( load_requested_packages(opts.packages) )
    available_filters_dict.update( get_available_filters_dict(loaded_modules) )
    
    files = remaining_args[1:] # remaining_args[0] seems to be sys.argv[0]
    
    if opts.do_list_filters:
        list_filters(available_filters_dict)
    
    filters = []
    
    filters_to_run = opts.filters_to_run # TODO: make filter instances from these and args
    for filter_name, args in filters_to_run:
        # TODO: handle key not in dict gracefully
        filter_class = available_filters_dict[filter_name]
        print filter_class
        print args
        filters.append(filter_class(*args))
    
    for file in files:
        for derivation in GuessReader(file):
            if opts.verbose: print >> sys.stderr, "Processing %s..." % derivation.label()
            
            for leaf in leaves(derivation.derivation):
                for filter in filters:
                    filter.accept_leaf(leaf)
                    
                    for comb, slash_index in izip(applications_per_slash(leaf), count()):
                        filter.accept_comb_and_slash_index(leaf, comb, slash_index)

            for filter in filters:
                filter.accept_derivation(derivation)
    
    for filter in filters:
        filter.output()
    
if __name__ == '__main__':
    main(sys.argv)