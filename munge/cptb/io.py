from itertools import izip, count
from munge.penn.parse import parse_tree

# Represents a derivation bundle in the Chinese Penn Treebank. This consists of a standard Penn 
# Treebank bracketing preceded by some additional SGML-like markup.
class Derivation(object):
    '''A derivation bundle contains the PTB derivation and its metadata.'''
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self.derivation = derivation
        
    def label(self):
        return "CTB:%d%02d(%d)" % (self.sec_no, self.doc_no, self.der_no)
    
import sys
from sgmllib import SGMLParser    
from collections import defaultdict
class SGMLBag(SGMLParser):
    def __init__(self):
        SGMLParser.__init__(self)

    def reset(self):
        SGMLParser.reset(self)
        self.fields = defaultdict(list)

    def handle_data(self, data):
        if self.topmost in ("p", "headline"):
            data = unicode(data, 'gb2312').encode('utf8')
            
        self.fields[self.topmost].append(data)
        
    def start_p(self, attrs):
        self.topmost = "p"
        self.topmost_attrs = None

    def unknown_starttag(self, tag, attrs):
        self.topmost = tag
        self.topmost_attrs = attrs

    def unknown_endtag(self, tag):
        self.topmost = self.topmost_attrs = None
        
    def __getitem__(self, key):
        return self.fields.get(key, None)
    
class CPTBReader(object):
    '''An iterator over a CPTB document yielding derivation bundles.'''
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        
        self.contents = SGMLBag()
        self.contents.feed(self.file.read())
        
        self.derivs = parse_tree('\n'.join(self.contents['p']))
        self.sec_no, self.doc_no = self.determine_sec_and_doc()
        
    def determine_sec_and_doc(self):
        ctb_id = self.contents['ctbid'][0]
        assert len(ctb_id) == 3
        
        return int(ctb_id[0]), int(ctb_id[1:])
        
    def __getitem__(self, index):
        for deriv in self:
            if deriv.der_no == index: return deriv
            
        return None
        
    def __iter__(self):
        for deriv, der_no in izip(self.derivs, count()):
            yield Derivation(self.sec_no, self.doc_no, der_no, deriv)
        
if __name__ == '__main__':
    from munge.trees.traverse import *

    r=CPTBReader('chtb_001.fid')
    
    for f in r:
        print ''.join(text(f.derivation))