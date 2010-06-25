import re
from itertools import imap, count, izip, islice

from munge.util.exceptions import CCGbankParseException
from munge.ccg.parse import parse_tree
from munge.io.single import SingleReader

class Derivation(object):
    '''Represents a single derivation inside a CCGbank document.'''
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self.derivation = derivation
        
    def label(self): 
        '''Returns a label representing this derivation.'''
        return "%0d:%d(%d)" % self.spec_tuple()

    def spec_tuple(self):
        return (self.sec_no, self.doc_no, self.der_no)
        
    def header(self):
        return "ID=wsj_%02d%02d.%d PARSER=GOLD NUMPARSE=1" % self.spec_tuple()
        
    def __str__(self):
        return '\n'.join((self.header(), str(self.derivation)))
    
    @staticmethod
    def from_header_and_derivation(header, deriv_string):
        '''Creates a Derivation object based on a header line and a derivation representation.
        This retrieves the section, document and derivation number from the header line,
        expecting it to be of the form 
        ID=wsj_SSDD.dd PARSER=GOLD NUMPARSE=1'''
        
        matches = re.match(r'ID=wsj_(\d\d)(\d\d).(\d+)', header)
        if matches and len(matches.groups()) == 3:
            sec_no, doc_no, der_no = [int(i) for i in matches.groups()]
            derivation = parse_tree(deriv_string)
        
            return Derivation(sec_no, doc_no, der_no, derivation)

        raise CCGbankParseException, "Malformed CCGbank header: %s" % header

class CCGbankReader(SingleReader):
    '''An iterator over each derivation in a CCGbank document.'''
    def __init__(self, filename):
        SingleReader.__init__(self, filename)
        
    def derivation_with_index(self, filename, index=None):
        self.file = open(filename, 'r')
        
        base = imap(lambda line: line.rstrip(), self.file.xreadlines())
        if index:
            return islice(base, 2*index - 2, 2*index)
        else:
            return base
                          
    def __getitem__(self, index):
        '''Index-based retrieval of a derivation.'''
        for deriv in self:
            if deriv.der_no == index: return deriv
            
        return None
                          
    def __iter__(self):
        '''Yields an iterator over this document.'''
        
        while True:
            try:
                header, deriv_string = self.derivs.next(), self.derivs.next()
            except StopIteration:
                self.file.close()
                raise
                
            yield Derivation.from_header_and_derivation(header, deriv_string)
            
    def __str__(self):
        raise NotImplementedError, "CCGbankReader cannot generate a string representation of its backing without consuming it."
            
class WritableCCGbankReader(object):
    def __init__(self, filename):
        self.reader = CCGbankReader(filename)
        self.derivs = list(self.reader)
        
    def __getitem__(self, index):
        for deriv in self.derivs:
            if deriv.der_no == index: return deriv
        return None
        
    def __setitem__(self, index, value):
        for deriv, i in izip(self.derivs, count()):
            if deriv.der_no == index: self.derivs[i] = value
        
    def __iter__(self):
        for deriv in self.derivs: yield deriv
        
    def __str__(self):
        return '\n'.join(str(bundle) for bundle in self.derivs)
