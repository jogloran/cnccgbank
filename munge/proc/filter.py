# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import re
class Option(object):
    @staticmethod
    def make_name(s):
        '''Convert a class name (like MyFilterName) into something easily typable on
the command line (like my-filter-name).
    Code adapted from Ruby on Rails (v3.1.0) method ActiveSupport::Inflector#underscore.'''
        s = re.sub(r'([A-Z]+)([A-Z][a-z])', r"\1-\2", s)
        s = re.sub(r'([a-z\d])([A-Z])'    , r"\1-\2", s)
        s = s.lower()
        return s

    def __init__(self, value=None):
        self.value = value
    def __get__(self, instance, owner):
        if self.value is None:
            return self.make_name(owner.__name__)
        return self.value
    def __set__(self, instance, value):
        self.value = value

class Filter(object):
    '''Every filter extends this class, which defines `don't care' implementations of the four hook
    functions. For each Derivation object (a bundle of the derivation object itself and some metadata),
    the framework calls each of the below methods.'''

    def __init__(self):
        # This will be set to the bundle object this filter is operating on.
        self.context = None
    
    accept_comb_and_slash_index = None
    # IMPORTANT: accept_comb_and_slash_index will not be called unless accept_leaf is defined as well.
    accept_leaf = None
    def accept_derivation(self, deriv): 
        '''This is invoked by the framework after each derivation is processed.'''
        pass
    def output(self): 
        '''This is invoked by the framework after all derivations have been processed.'''
        pass

    # Concrete filters should define a long name ('--long-name') for command-line invocation.
    long_opt = Option()
    # Concrete filters should define a short name ('-l') for command-line invocation.
    opt = '?'
    
    # This is displayed after the long name as an intuitive name for any arguments the filter may expect.
    arg_names = ''
    
    @staticmethod
    def is_abstract(): return False
    