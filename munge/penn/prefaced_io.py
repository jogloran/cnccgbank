import re

from munge.util.exceptions import CCGbankParseException
from munge.penn.parse import parse_tree, AugmentedPennParser
from munge.io.single import SingleReader
from munge.util.err_utils import warn
from itertools import imap
from munge.util.str_utils import nth_occurrence

import munge.penn.io as B

class Derivation(B.Derivation):
    '''Represents a single derivation inside a PTB document.'''
    @staticmethod
    def from_header_and_derivation(header, deriv_string):
        matches = re.match(r'ID=wsj_(\d\d)(\d\d).(\d+)', header)
        if matches and len(matches.groups()) == 3:
            sec_no, doc_no, der_no = [int(i) for i in matches.groups()]
            derivation = parse_tree(deriv_string, AugmentedPennParser)[0]

            ret = Derivation(sec_no, doc_no, der_no, derivation)
            return ret

        raise CCGbankParseException, "Malformed CCGbank header: %s" % header
        
class PrefacedPTBReader(B.AugmentedPTBReader):
    '''An iterator over each derivation in a PTB document.'''
    def __init__(self, filename):
        self.sec_no, self.doc_no = self.determine_sec_and_doc(filename)
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
            
    def __iter__(self):
        '''Yields an iterator over this document.'''
        while True:
            try:
                header, deriv_string = self.derivs.next(), self.derivs.next()
            except StopIteration:
                self.file.close()
                raise

            yield Derivation.from_header_and_derivation(header, deriv_string)

