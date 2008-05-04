import os
import re

from munge.penn.parse import parse_tree
from itertools import izip, count

class Derivation(object):
    '''Represents a single derivation inside a PTB document.'''
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self.derivation = derivation
        
    def label(self): 
        '''Returns a label representing this derivation.'''
        return "%0d:%d(%d)" % (self.sec_no, self.doc_no, self.der_no)
        
    def __str__(self):
        return str(self.derivation)
        
class PTBReader(object):
    '''An iterator over each derivation in a PTB document.'''
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        self.derivs = parse_tree(self.file.read())
        
        self.sec_no, self.doc_no = self.determine_sec_and_doc(filename)
        
    def determine_sec_and_doc(self, filename):
        '''Determines the section and document number given a filename of the form ``wsj_SSDD.mrg".'''
        matches = re.match(r'wsj_(\d\d)(\d\d)\.(?:.+)', os.path.basename(filename))
        if matches and len(matches.groups()) == 2:
            return (int(i) for i in matches.groups())
        else:
            # TODO: Should ideally be a warning condition
            return 0, 0
    
    def __getitem__(self, index):
        '''Index-based retrieval of a derivation. Note that derivations are 1-indexed, in line with their derivation IDs.'''
        if index < 1: return None
        try:
            return self.derivs[index-1]
        except IndexError: return None
                
    def __setitem__(self, index, deriv):
        '''Index-based modification of a derivation. 1-indexed like getitem.'''
        try:
            self.derivs[index-1] = deriv
        except IndexError: pass
        
    def __iter__(self):
        '''Yields an iterator over this document.'''
        # Number derivations starting from 1, in common with CCGbank IDs
        for deriv, der_no in izip(self.derivs, count(1)):
            yield Derivation(self.sec_no, self.doc_no, der_no, deriv)