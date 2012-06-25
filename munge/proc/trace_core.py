# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import sys
import os
import errno
import re

from munge.io.guess import GuessReader
from munge.io.multi import DirFileGuessReader
from munge.penn.io import AugmentedPTBReader, CategoryPTBReader
from munge.penn.prefaced_io import PrefacedPTBReader
from munge.cptb.io import CPTBHeadlineReader
from munge.io.paired import PairedReader

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
        
        self.verbose = verbose
        self.reader_class_name = reader_class_name
        
        self.last_exceptions = []
        self._break_on_exception = break_on_exception
        
    @property
    def verbose(self): return self._verbose
    @verbose.setter
    def verbose(self, v):
        self._verbose = v
        muzzle(quiet=not self._verbose)
    
    @property
    def break_on_exception(self): return self._break_on_exception
    @break_on_exception.setter
    def break_on_exception(self, v): self._break_on_exception = v

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

        print >>sys.stderr, "%d packages loaded (%s), %d filters available:" % (len(self.loaded_modules), 
                                                                  ", ".join(mod.__name__ for mod in self.loaded_modules),
                                                                  len(self.available_filters_dict))
                                                                  
        for (filter_name, filter) in sorted(self.available_filters_dict.iteritems(), key=sort_key_function):
            print >>sys.stderr, template_function(filter_name, filter)

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
                err("No filter with name `%s' found.", filter_name)
                
        # convert short notation in file specifiers to proper paths
        def expand_short_notation(fn):
            # short notation is 
            # corpus:ss,dd,deriv -> corpus/chtb_ssdd.fid:deriv
            m = re.match(r'([^:]+):(\d+),(\d+),(\d+)', fn)
            if m:
                corpus_dir, sec, doc, deriv = m.groups()
                return os.path.join(corpus_dir, 'chtb_%02d%02d.fid:%d' % (int(sec), int(doc), int(deriv)))
            return fn
            
        files = [expand_short_notation(file) for file in files]

        self.run_filters(filters, files)
        
    @staticmethod
    def is_pair_spec(file):
        def is_file_or_dir(f):
            return os.path.isdir(f) or os.path.isfile(f)
        bits = file.split('~', 2)
        if len(bits) != 2: return False
        return is_file_or_dir(bits[0]) and is_file_or_dir(bits[1])
        
    @classmethod
    def transform(cls, files):
        '''Maps a sequence of derivation specifiers, each of the form sec:doc(deriv) or
phase/sec:doc(deriv) to full PCTB paths.'''
        def transform_element(fn):
            # TODO: This is not robust and only works for PCTB
            matches = (re.match(r'''(?:([^/]+)/)? # optional: phase name then '/'
                                   (\d+):(\d+)\((\d+)\) # deriv id
                                   ''', fn, flags=re.VERBOSE)
                       or
                       re.match(r'''(?:([^/]+)/)?
                                    (\d{1,2}).*?(\d{1,2}).*?(\d+)
                                    ''', fn, flags=re.VERBOSE))
            if matches:
                phase = matches.group(1) or 'cn'
                sec, doc, deriv = map(int, matches.groups()[1:])
                return os.path.join(phase, 'chtb_%02d%02d.fid:%d' % (
                    sec, doc, deriv
                ))
            return fn
        return (transform_element(fn) for fn in files)

    def run_filters(self, filters, files):
        # If all given filters were not found or had wrong argument count, do nothing
        if not filters: return
        
        reader_args = {}
        if self.reader_class_name:
            try:
                reader_class = globals()[self.reader_class_name]
                info("Using reader class %s.", self.reader_class_name)
                
                reader_args['reader_class'] = reader_class
            except KeyError:
                raise RuntimeError("Reader class %s not found." % self.reader_class_name)
        
        for file in self.transform(files):
            if self.is_pair_spec(file):
                meta_reader = PairedReader
            else:
                meta_reader = DirFileGuessReader
                
            try:
                self.last_exceptions = []
                
                for derivation_bundle in meta_reader(file, verbose=self.verbose, **reader_args):
                    if self.verbose: info("Processing %s...", derivation_bundle.label())
                    try:
                        for filter in filters:
                            filter.context = derivation_bundle

                        if filter.accept_leaf is not None:
                            for leaf in leaves(derivation_bundle.derivation):
                                for filter in filters:
                                    filter.accept_leaf(leaf)

                                    if filter.accept_comb_and_slash_index is not None:
                                        try:
                                            for slash_index, comb in enumerate(applications_per_slash(leaf)):
                                                filter.accept_comb_and_slash_index(leaf, comb, slash_index)
                                        except AttributeError: # TODO: hacky and inefficient, need this to work for PTB too
                                            pass

                        for filter in filters:
                            filter.accept_derivation(derivation_bundle)
                            filter.context = None
                            
                    except IOError, e:
                        # If output is going to a pager, and the user requests an interrupt (^C)
                        # the filter fails with IOError: Broken pipe
                        # In that case, running filters on further derivations will continue to
                        # lead to 'Broken pipe', so just bail out
                        if e.errno == errno.EPIPE: return
                            
                    except Exception, e:
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
                    
            except IOError, e:
                for bundle, exception in self.last_exceptions:
                    err("Processing failed on derivation %s of file %s:", bundle.label(), file)
                    sys.excepthook(*exception)
                err("Processing failed with IOError: %s", e)
                raise

        for filter in filters:
            filter.output()
            if self.verbose:
                print >>sys.stderr, "---"
