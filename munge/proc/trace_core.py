from itertools import izip, count

from munge.io.guess import GuessReader
from munge.io.multi import DirFileGuessReader
from munge.trees.traverse import leaves
from munge.cats.paths import applications_per_slash
from munge.proc.dynload import (get_available_filters_dict, 
                                load_requested_packages,
                                get_argcount_for_method)

class TraceCore(object):
    def __init__(self, libraries, verbose=True):
        self.loaded_modules = set(load_requested_packages(libraries))
        self.available_filters_dict = get_available_filters_dict(self.loaded_modules)
        
        self.verbose = verbose
        
    def list_filters(self):
        '''Prints a list of all the filters loaded, with a summary of the number and role of the arguments
each filter takes.'''
        print "%d packages loaded (%s), %d filters available:" % (len(self.loaded_modules), 
                                                                  ", ".join(mod.__name__ for mod in self.loaded_modules),
                                                                  len(self.available_filters_dict))
        for (filter_name, filter) in sorted(self.available_filters_dict.iteritems(), key=lambda (name, filter): name):
            print "\t%s\n\t\t(%d args, -%s, --%s%s)" % (filter_name, 
                                                 get_argcount_for_method(filter.__init__), 
                                                 filter.opt, 
                                                 filter.long_opt,
                                                 (' '+filter.arg_names) if filter.arg_names else '')
                                                 
    def add_modules(self, module_names):
        '''Attempts to load new filters, as specified by a list of module names.'''
        self.loaded_modules.update(load_requested_packages(module_names))
        
    def run(self, filters_to_run, files):
        '''Performs a processing run, given a list of filter names to run, and a list of file specifiers.'''
        filters = []
        
        for filter_name, args in filters_to_run:
            # For a no-args switch, optparse passes in None; we substitute an empty tuple for
            # consistency
            if not args: args = ()

            try:
                filter_class = self.available_filters_dict[filter_name]
                filters.append(filter_class(*args))
            except KeyError:
                warn("No filter with name `%s' found.", filter_name)

        for file in files:
            if self.verbose: info("Processing %s...", file)
            for derivation_bundle in DirFileGuessReader(file):
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
