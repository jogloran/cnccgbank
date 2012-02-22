# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import re, os
from itertools import imap, islice

from munge.util.exceptions import CCGbankParseException
from munge.ccg.parse import parse_tree
from munge.io.single import SingleReader
from munge.util.str_utils import nth_occurrence

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
    def determine_sec_and_doc(self, filename):
        matches = re.match(r'chtb_(\d{4})\..+', os.path.basename(filename))
        if matches:
            file_id = matches.group(1)
            return int(file_id[:2]), int(file_id[2:])
        return None
        
    def __init__(self, filename):
        sec_and_doc = self.determine_sec_and_doc(filename)
        if sec_and_doc:
            self.sec_no, self.doc_no = sec_and_doc

        SingleReader.__init__(self, filename)
        
    def derivation_with_index(self, filename, index=None):
        self.file = open(filename, 'r')
        
        base = imap(lambda line: line.rstrip(), self.file.xreadlines())
        if index:
            lines = nth_occurrence(base,
                                  N=1,
                                  # put a space after the pattern to ensure we match the whole token
                                  when=lambda line: re.match(r"^ID=wsj_%02d%02d.%d " % (self.sec_no, self.doc_no, index), line),
                                  until=lambda line: re.match(r"^ID", line))
            return iter(lines)
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
        for i, deriv in enumerate(self.derivs):
            if deriv.der_no == index: self.derivs[i] = value
        
    def __iter__(self):
        for deriv in self.derivs: yield deriv
        
    def __str__(self):
        return '\n'.join(str(bundle) for bundle in self.derivs)
