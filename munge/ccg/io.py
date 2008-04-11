import re

from munge.util.exceptions import CCGbankParseException
from munge.ccg.parse import parse_tree

from itertools import imap

class Derivation(object):
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self.derivation = derivation
        
    @staticmethod
    def from_header_and_derivation(header, deriv_string):
        matches = re.match(r'ID=wsj_(\d\d)(\d\d).(\d+) PARSER=GOLD NUMPARSE=1', header)
        if matches:
            if len(matches.groups()) != 3:
                raise CCGbankParseException, "Malformed CCGbank header: %s" % header
            sec_no, doc_no, der_no = [int(i) for i in matches.groups()]
            
            derivation = parse_tree(deriv_string)
        
            return Derivation(sec_no, doc_no, der_no, derivation)
            
        return None

class CCGbankReader(object):
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        self.lines = imap(lambda line: line[0:-1] if line[-1] == '\n' else line,
                          self.file.xreadlines())
        
    def __iter__(self):
        while True:
            try:
                header, deriv_string = self.lines.next(), self.lines.next()
            except StopIteration:
                self.file.close()
                raise
                
            yield Derivation.from_header_and_derivation(header, deriv_string)

            