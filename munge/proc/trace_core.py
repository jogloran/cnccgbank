import sys

from itertools import izip, count

from munge.io.guess import GuessReader
from munge.io.multi import DirFileGuessReader
from munge.penn.io import AugmentedPTBReader

from munge.trees.traverse import leaves
from munge.cats.paths import applications_per_slash
from munge.proc.dynload import (get_available_filters_dict,
                                load_requested_packages,
                                get_argcount_for_method)
from munge.util.err_utils import warn, info, err, muzzle
from munge.util.exceptions import FilterException

class TraceCore(object):
    '''Implements filter loading functionality and the document processing loop.'''
    def __init__(self, libraries, verbose=True, break_on_exception=False, reader_class_name=None):
        self.loaded_modules = set(load_requested_packages(libraries))
        self.update_available_filters_dict()
        
        self.set_verbose(verbose)
        self.reader_class_name = reader_class_name
        
        self.last_exceptions = []
        self.set_break_on_exception(break_on_exception)
        
    def get_verbose(self): return self._verbose
    def set_verbose(self, v):
        self._verbose = v
        muzzle(quiet=not self._verbose)
    verbose = property(get_verbose, set_verbose)
    
    def get_break_on_exception(self): return self._break_on_exception
    def set_break_on_exception(self, v): self._break_on_exception = v
    break_on_exception = property(get_break_on_exception, set_break_on_exception)

    def __getitem__(self, key):
        return self.available_filters_dict.get(key, None)
        
    def __contains__(self, key):
        return key in self.available_filters_dict
        
    def update_available_filters_dict(self):
        self.available_filters_dict = get_available_filters_dict(self.loaded_modules)

    def list_filters(self, long=True, filter_sort_key=None):
        '''Prints a list of all the filters loaded, in long or short form, sorted by the given key.'''
        def LongTemplate(filter_name, filter):
            return ("\t%s (%s)\n\t\t(%d args, -%s, --%s%s)" % 
                        (filter_name, filter.__module__,
                         get_argcount_for_method(filter.__init__), 
                         filter.opt, filter.long_opt,
                         (' '+filter.arg_names) if filter.arg_names else ''))
                                                         
        def ShortTemplate(filter_name, filter):
            return "\t% 30s. %s(%s) {%s, %s}" % \
                (filter.__module__, filter_name, filter.arg_names,
                 filter.opt, filter.long_opt)

        template_function = { True: LongTemplate, False: ShortTemplate }[long]
        
        sort_by_name = lambda (name, filter): name
        sort_key_function = {
            'name': sort_by_name,
            'module': lambda (name, filter): filter.__module__,
            'opt': lambda (name, filter): filter.opt,
            'long-opt': lambda (name, filter): filter.long_opt
        }.get(filter_sort_key, sort_by_name)

        print "%d packages loaded (%s), %d filters available:" % (len(self.loaded_modules), 
                                                                  ", ".join(mod.__name__ for mod in self.loaded_modules),
                                                                  len(self.available_filters_dict))
                                                                  
        for (filter_name, filter) in sorted(self.available_filters_dict.iteritems(), key=sort_key_function):
            print template_function(filter_name, filter)

    def add_modules(self, module_names):
        '''Attempts to load new filters, as specified by a list of module names.'''
        self.loaded_modules.update(load_requested_packages(module_names))
        self.update_available_filters_dict()

    def run(self, filters_to_run, files):
        '''Performs a processing run, given a list of filter names to run, and a list of file specifiers.'''
        filters = []

        for filter_name, args in filters_to_run:
            # For a no-args switch, optparse passes in None; we substitute an empty tuple for
            # consistency
            if not args: args = ()

            try:
                filter_class = self.available_filters_dict[filter_name]
                
                actual, expected = len(args), get_argcount_for_method(filter_class.__init__)
                if actual != expected:
                    warn("Skipping filter %s; %d arguments given, %d expected.", filter_name, actual, expected)
                    continue
                    
                filters.append(filter_class(*args))
            except KeyError:
                warn("No filter with name `%s' found.", filter_name)

        self.run_filters(filters, files)

    def run_filters(self, filters, files):
        # If all given filters were not found or had wrong argument count, do nothing
        if not filters: return
        
        reader_class = None
        if self.reader_class_name:
            try:
                reader_class = globals()[self.reader_class_name]
                info("Using reader_class %s.", self.reader_class_name)
            except KeyError:
                err("Reader class %s not found.", self.reader_class_name)
        
        for file in files:
            try:
                self.last_exceptions = []
                
                for derivation_bundle in DirFileGuessReader(file, verbose=self.verbose, reader_class=reader_class):
                    if self.verbose: info("Processing %s...", derivation_bundle.label())
                    try:
                        for filter in filters:
                            filter.context = derivation_bundle

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
                            filter.context = None
                            
                    except Exception, e:
                        # import pdb
                        # pdb.set_trace()
                        self.last_exceptions.append( (derivation_bundle, sys.exc_info()) )
                        
                        if self._break_on_exception:
                            raise FilterException(e, None)
                else:
                    if self.last_exceptions:
                        raise FilterException(e, None)
                        
            except FilterException, e:
                for bundle, exception in self.last_exceptions:
                    err("Processing failed on derivation %s of file %s:", bundle.label(), file)
                    sys.excepthook(*exception)

        for filter in filters:
            filter.output()
            print "---"
