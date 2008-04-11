import re
from itertools import imap

from munge.util.exceptions import CCGbankParseException
from munge.ccg.parse import parse_tree

class Derivation(object):
    '''Represents a single derivation inside a CCGbank document.'''
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self.derivation = derivation
        
    def label(self): 
        '''Returns a label representing this derivation.'''
        return "%2d:%2d(%d)" % (self.sec_no, self.doc_no, self.der_no)
    
    @staticmethod
    def from_header_and_derivation(header, deriv_string):
        '''Creates a Derivation object based on a header line and a derivation representation.
        This retrieves the section, document and derivation number from the header line,
        expecting it to be of the form 
        ID=wsj_SSDD.dd PARSER=GOLD NUMPARSE=1'''
        matches = re.match(r'ID=wsj_(\d\d)(\d\d).(\d+) PARSER=GOLD NUMPARSE=1', header)
        if matches:
            if len(matches.groups()) != 3:
                raise CCGbankParseException, "Malformed CCGbank header: %s" % header
            sec_no, doc_no, der_no = [int(i) for i in matches.groups()]
            
            derivation = parse_tree(deriv_string)
        
            return Derivation(sec_no, doc_no, der_no, derivation)
            
        return None

class CCGbankReader(object):
    '''An iterator over each derivation in a CCGbank document.'''
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        self.lines = imap(lambda line: line[0:-1] if line[-1] == '\n' else line,
                          self.file.xreadlines())
                          
    def __getitem__(self, index):
        '''Index-based retrieval of a derivation.'''
        for deriv in self:
            if deriv.der_no == index: return deriv
            
        return None
                          
    def __iter__(self):
        '''Yields an iterator over this document.'''
        while True:
            try:
                header, deriv_string = self.lines.next(), self.lines.next()
            except StopIteration:
                self.file.close()
                raise
                
            yield Derivation.from_header_and_derivation(header, deriv_string)

            