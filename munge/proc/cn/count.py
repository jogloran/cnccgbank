from __future__ import with_statement
from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from collections import defaultdict
from munge.util.dict_utils import sorted_by_value_desc
import os, re

def last_nonpunct_kid(node):
    if node.is_leaf(): return None
    
    for kid in node.kids[::-1]:
        if not kid.tag.startswith('PU'): return kid
        
    return None

PredicationRegex = re.compile(r'''
    (?:\w+)?
    (\s+\w+\s*)* # adjuncts
    [\w-]+-SBJ\s+ # grammatical subject
    VP # predicate
''', re.VERBOSE)
def is_predication(node):
    kid_tags = ' '.join(kid.tag for kid in node)
    return node.tag.startswith('IP') and PredicationRegex.match(kid_tags)

def is_apposition(node):
    return node.tag.startswith('NP') and last_nonpunct_kid(node).tag.startswith('NP') and node[0].tag.endswith('-APP')
    
FunctionTags = 'ADV TPC TMP LOC DIR BNF CND DIR IJ LGS MNR PRP'.split()

def is_modification(node):
    if node.tag == last_nonpunct_kid(node).tag:
        return has_modification_tag(node[0])
    
    return False
    
def has_modification_tag(node):
    m = re.match(r'\w+-(\w+)', node.tag)
    if m and len(m.groups()) == 1:
        function_tag = m.group(1)
        if function_tag in FunctionTags: return True
    return False
    
CoordinationRegex = re.compile(r'(?:(?:PU|CC)?\s*)+([\w:]+)(?: (?:(?:PU|CC)?\s*)+\1)+')

def is_coordination(node):
    if not any(kid.tag in ('CC', 'PU') for kid in node): return False
    kid_tags = ' '.join(kid.tag for kid in node)
    return CoordinationRegex.match(kid_tags)
    

def is_internal_structure(node):
    return all(kid.is_leaf() for kid in node)
    
class TagStructures(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if not node.is_leaf():
                last_kid = last_nonpunct_kid(node)
                
                if is_predication(node):
                    for kid in node:
                        if kid.tag.endswith('-SBJ'):
                            kid.tag += ':l' # TODO: is subject always left of predicate?
                        elif kid.tag == 'VP':
                            kid.tag += ':h'
                        elif kid.tag != 'PU':
                            kid.tag += ':a'
                    
                elif is_coordination(node): # coordination
                    for kid in node:
                        if kid.tag not in ('CC', 'PU'):
                            kid.tag += ':c'

                elif is_internal_structure(node):
                    pass

                elif node[0].is_leaf(): # head initial complementation
                    node[0].tag += ':h'
                    for kid in node[1:node.count()]:
                        if kid.tag.startswith('AS'):
                            kid.tag += ':a' # treat aspect particles as adjuncts
                        elif not kid.tag.startswith('PU'):
                            kid.tag += ':r'

                elif last_kid.is_leaf(): # head final complementation
                    last_kid.tag += ':h'
                    for kid in node[0:node.count()-1]:
                        if kid.tag.startswith('AS'):
                            kid.tag += ':a' # treat aspect particles as adjuncts
                        elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                            kid.tag += ':l'

                elif is_apposition(node):
                    for kid in node:
                        if not kid.tag.startswith('PU'):
                            kid.tag += ':A'

                elif is_modification(node):
                    last_kid.tag += ':h'
                    
                    for kid in node[0:node.count()-1]:
                        if not kid.tag.endswith(':h'):
                            if has_modification_tag(kid):
                                kid.tag += ':m'
                            elif not kid.tag.startswith('PU'):
                                kid.tag += ':a'

                else: # adjunction
                    last_kid.tag += ':h'
                    for kid in node[0:node.count()-1]:
                        if not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                            kid.tag += ':a'

        self.write_derivation(bundle)

    def write_derivation(self, bundle):
        if not os.path.exists(self.outdir): os.makedirs(self.outdir)
        output_filename = os.path.join(self.outdir, "chtb_%02d%02d.fid" % (bundle.sec_no, bundle.doc_no))

        with file(output_filename, 'a') as f:
            print >>f, bundle.derivation

class CountStructures(Filter):
    def __init__(self):
        Filter.__init__(self)
        
        self.counts = defaultdict(lambda: 0)
        self.adjunction_kinds = defaultdict(lambda: 0)
        self.predication_kinds = defaultdict(lambda: 0)
        self.apposition_kinds = defaultdict(lambda: 0)
        self.modification_kinds = defaultdict(lambda: 0)
        self.coordination_kinds = defaultdict(lambda: 0)
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if not node.is_leaf():
                self.counts['total'] += 1
                kid_tags = ' '.join(kid.tag for kid in node)
                
                if is_predication(node):
                    self.counts['predication'] += 1
                    self.predication_kinds[kid_tags] += 1
                
                elif is_coordination(node): # coordination
                    self.counts['coordination'] += 1
                    self.coordination_kinds[kid_tags] += 1
                    
                elif is_internal_structure(node):
                    self.counts['structure'] += 1
                    
                elif node[0].is_leaf(): # head initial complementation
                    self.counts['head-initial'] += 1

                elif node[-1].is_leaf(): # head final complementation
                    self.counts['head-final'] += 1
                    
                elif is_apposition(node):
                    self.counts['apposition'] += 1
                    self.apposition_kinds[kid_tags] += 1
                    
                elif is_modification(node):
                    self.counts['modification'] += 1
                    self.modification_kinds[kid_tags] += 1
                    
                else: # adjunction
                    self.counts['adjunction'] += 1
                    self.adjunction_kinds[kid_tags] += 1
    
                    
    def output(self):
        for node_type, count in sorted_by_value_desc(self.counts):
            if node_type == 'total': continue
            print "% 15s | %d" % (node_type, count)
        print "% 15s | %d" % ('total', self.counts['total'])
        print
        
        for dict_name in ('predication', 'apposition', 'modification', 'adjunction', 'coordination'):
            print dict_name
            for tag_string, count in sorted_by_value_desc(getattr(self, dict_name + '_kinds')):
                print "% 6d | (% 2d) %s" % (count, len(tag_string.split(' ')), tag_string)
            print
        
class CountWords(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.n = 0
        
    def accept_leaf(self, leaf):
        self.n += 1
        
    def output(self):
        print self.n
        
