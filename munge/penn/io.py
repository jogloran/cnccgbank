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
        
class PTBReader(object):
    '''An iterator over each derivation in a PTB document.'''
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        self.derivs = parse_tree(self.file.read())
        
        self.sec_no, self.doc_no = self.determine_sec_and_doc(filename)
        
    def determine_sec_and_doc(self, filename):
        matches = re.match(r'wsj_(\d\d)(\d\d)\.(?:.+)', os.path.basename(filename))
        if matches and len(matches.groups()) == 2:
            return (int(i) for i in matches.groups())
        else:
            # TODO: Should ideally be a warning condition
            return 0, 0
    
    def __getitem__(self, index):
        '''Index-based retrieval of a derivation.'''
        for deriv in self:
            if deriv.der_no == index: return deriv
            
        return None
        
    def __iter__(self):
        '''Yields an iterator over this document.'''
        for deriv, der_no in izip(self.derivs, count()):
            yield Derivation(self.sec_no, self.doc_no, der_no, deriv)