# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.penn.parse import parse_tree, AugmentedPennParser
from munge.io.single import SingleReader
from munge.util.str_utils import nth_occurrence
from munge.util.exceptions import CPTBParseException
import re, os

# Represents a derivation bundle in the Chinese Penn Treebank. This consists of a standard Penn 
# Treebank bracketing preceded by some additional SGML-like markup.
class Derivation(object):
    '''A derivation bundle contains the PTB derivation and its metadata.'''
    def __init__(self, sec_no, doc_no, der_no, derivation):
        self.sec_no, self.doc_no, self.der_no = sec_no, doc_no, der_no
        self.derivation = derivation

    def spec_tuple(self):
        return (self.sec_no, self.doc_no, self.der_no)
        
    def label(self):
        return "%0d:%d(%d)" % self.spec_tuple()
    
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
    
class CPTBReader(SingleReader):
    '''An iterator over a CPTB document yielding derivation bundles.'''
    def __init__(self, filename):
        SingleReader.__init__(self, filename)
                
        self.sec_no, self.doc_no = self.determine_sec_and_doc()
        
    def derivation_with_index(self, filename, i=None):
        self.contents = SGMLBag()
        with open(filename, 'r') as file:
            if i:
                text = ''.join(nth_occurrence(file.xreadlines(),
                                      N=i,
                                      when=lambda line: re.match(r'^<S', line),
                                      until=lambda line: re.match(r'^</S', line)))
            else:
                text = file.read()
                
            self.contents.feed(text)
        
        # HACK HACK HACK:
        # Sometimes <S>...</S> encloses more than one root (3:7 has some);
        # in which case, counting <S> will undercount the number of sentences
        if self.contents['s'] is None: return parse_tree('', AugmentedPennParser)
        
        return parse_tree('\n'.join(self.contents['s']), AugmentedPennParser)
        
    def determine_sec_and_doc(self):
        ctb_value = self.contents['ctbid']
        if ctb_value:
            ctb_id = ctb_value[0]
            assert len(ctb_id) == 3
            return int(ctb_id[0]), int(ctb_id[1:])
        else:
            # ctbid element seems to have disappeared between versions 2 and 6
            # try to discover it from the filename
            matches = re.match(r'chtb_(\d{4})\..+', os.path.basename(self.filename))
            file_id = matches.group(1)
            return int(file_id[:2]), int(file_id[2:])
        
    def __getitem__(self, index):
        for deriv in self:
            if deriv.der_no == index: return deriv
            
        return None
        
    def __iter__(self):
        for der_no, deriv in enumerate(self.derivs, 1):
            yield Derivation(self.sec_no, self.doc_no, self.index or der_no, deriv)

class CPTBHeadlineReader(CPTBReader):
    '''Only returns derivations between <HEADLINE> tags. If you force this Reader, remember that
this will fail on files which aren't CPTB formatted.'''

    def __init__(self, filename):
        SingleReader.__init__(self, filename)
        self.sec_no, self.doc_no = self.determine_sec_and_doc()

    def derivation_with_index(self, filename, i=None):
        self.contents = SGMLBag()
        with open(filename, 'r') as file:
            headline_lines = nth_occurrence(file, N=1, 
                             when=lambda line:  re.match(r'^<HEADLINE', line),
                             until=lambda line: re.match(r'^</HEADLINE', line))
            if not headline_lines: return None

            if not headline_lines[0].startswith('<HEADLINE'):
                raise CPTBParseException('Expected to find a <HEADLINE> line.')
                
            headline_lines = headline_lines[1:] # strip off <HEADLINE>
            if i:
                text = ''.join(headline_lines[i])
            else:
                text = '\n'.join(headline_lines)

            self.contents.feed(text)

        return parse_tree('\n'.join(self.contents['s']), AugmentedPennParser)