import os
import re

from munge.penn.parse import parse_tree, PennParser
from munge.util.err_utils import warn
from itertools import izip, count
from munge.util.str_utils import padded_rsplit

from munge.io.single import SingleReader
from munge.util.str_utils import nth_occurrence

class Derivation(object):
    '''Represents a single derivation inside a PTB document.'''
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self._derivation = derivation
        
    def spec_tuple(self):
        return (self.sec_no, self.doc_no, self.der_no)
        
    def label(self): 
        '''Returns a label representing this derivation.'''
        return "%0d:%d(%d)" % self.spec_tuple()
        
    def get_derivation(self): return self._derivation
    def set_derivation(self, derivation): self._derivation = derivation
    derivation = property(get_derivation, set_derivation)
        
    def __str__(self):
        return str(self.derivation)
        
class PTBReader(SingleReader):
    '''An iterator over each derivation in a PTB document.'''
    def __init__(self, filename):
        SingleReader.__init__(self, filename)
        self.sec_no, self.doc_no = self.determine_sec_and_doc(filename)
        
    def derivation_with_index(self, filename, index=None):
        with open(filename, 'r') as file:
            if index:
                return self.parse_file(''.join(
                    nth_occurrence(file.xreadlines(),
                                      N=index, 
                                      when=lambda line: re.match(r"^\(", line),
                                      until=lambda line: re.match(r"^\(", line))))
            else:
                return self.parse_file(file.read())
        
    @staticmethod
    def parse_file(text):
        return parse_tree(text, PennParser)
        
    def determine_sec_and_doc(self, filename):
        '''Determines the section and document number given a filename of the form ``wsj_SSDD.mrg".'''
        matches = re.match(r'(?:.+)_(\d\d)(\d\d)\.(?:.+)', os.path.basename(filename))
        if matches and len(matches.groups()) == 2:
            return (int(i) for i in matches.groups())
        else:
            warn("Skipping malformed section/document specifier: `%s'", filename)
            return 0, 0
    
    def __getitem__(self, index):
        '''Index-based retrieval of a derivation. Note that derivations are 1-indexed, in line with their derivation IDs.'''
        if index < 1: return None
        try:
            # if we are in single-mode, use the index passed in
            return Derivation(self.sec_no, self.doc_no, (self.index or index), self.derivs[index-1])
        except IndexError: return None
                
    def __setitem__(self, index, deriv):
        '''Index-based modification of a derivation. 1-indexed like getitem.'''
        try:
            self.derivs[index-1] = deriv.derivation
        except IndexError: pass
        
    def __iter__(self):
        '''Yields an iterator over this document.'''
        # Number derivations starting from 1, in common with CCGbank IDs
        for der_no, deriv in enumerate(self.derivs, 1):
            yield Derivation(self.sec_no, self.doc_no, (self.index or der_no), deriv)
            
    def __str__(self):
        '''Returns the text of an entire document.'''
        return '\n'.join(str(deriv) for deriv in self.derivs)

from munge.penn.parse import AugmentedPennParser
class AugmentedPTBReader(PTBReader):
    def __init__(self, *args):
        PTBReader.__init__(self, *args)

    @staticmethod
    def parse_file(text):
        return parse_tree(text, AugmentedPennParser)

from munge.penn.parse import CategoryPennParser
class CategoryPTBReader(PTBReader):
    def __init__(self, *args):
        PTBReader.__init__(self, *args)

    @staticmethod
    def parse_file(text):
        return parse_tree(text, CategoryPennParser, "()", "")
