from __future__ import with_statement
from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from collections import defaultdict
from munge.util.dict_utils import sorted_by_value_desc
import os, re

def last_nonpunct_kid(node):
    kid, index = get_nonpunct_kid(node)
    return kid
    
def get_nonpunct_kid(node, get_last=True):
    if node.is_leaf(): return None, None
    
    if get_last:
        for i, kid in enumerate(node.kids[::-1]):
            if not kid.tag.startswith('PU'): return kid, node.count() - i - 1
    else:
        for i, kid in enumerate(node.kids):
            if not kid.tag.startswith('PU'): return kid, i
        
    return None, None

PredicationRegex = re.compile(r'''
    (?:\w+)?
    (\s+\w+\s*)* # adjuncts
    [\w-]+-SBJ\s+ # grammatical subject
    (?:PU\s+)?
    VP # predicate
''', re.VERBOSE)
def is_predication(node):
    kid_tags = ' '.join(kid.tag for kid in node)
    return node.tag.startswith('IP') and PredicationRegex.match(kid_tags)

def is_apposition(node):
#    return node.tag.startswith('NP') and last_nonpunct_kid(node).tag.startswith('NP') and node[0].tag.endswith('-APP')
    return node.tag.startswith('NP') and any(kid.tag.endswith('-APP') for kid in node)
    
FunctionTags = 'ADV TMP LOC DIR BNF CND DIR IJ LGS MNR PRP'.split()

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
    
# coordination is
# (PU spaces)+ (conjunct)( (PU spaces) conjunct)+
CoordinationRegex = re.compile(r'(?:(?:PU|CC) )*([\w:]+)(?: (?:(?:PU|CC) )+\1)+')

def is_coordination(node):
    if not any(kid.tag in ('CC', 'PU') for kid in node): return False
    kid_tags = ' '.join(kid.tag for kid in node)
#    return CoordinationRegex.match(kid_tags)
    return CoordinationRegex.search(kid_tags)
    
def is_internal_structure(node):
    return all(kid.is_leaf() for kid in node)
    
def is_np_internal_structure(node):
    return node.tag.startswith('NP') and node.count() > 1 and (
        all(kid.tag in ('NN', 'NR', 'NT', 'PU') for kid in node))
    
def is_vp_internal_structure(node):
    return node.count() > 1 and all(kid.tag in ('VV', 'VA', 'VC', 'VE') for kid in node)
    
def is_lcp_internal_structure(node):
    if not node.count() == 2: return False
    return node[0].tag == 'NP' and node[1].tag == 'LC'
    
class TagStructures(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir
        
    def is_postverbal_adjunct_tag(self, tag):
        return tag.startswith('AS') or tag.startswith('DER')
        
    @staticmethod
    def tag(kid, tag):
        # make sure kid is not already tagged
        if len(kid.tag) >= 2 and kid.tag[-2] == ':': return
        
        kid.tag += (':' + tag)
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if not node.is_leaf():
                first_kid, first_kid_index = get_nonpunct_kid(node, get_last=False)
                last_kid,  last_kid_index  = get_nonpunct_kid(node, get_last=True)
                
                for kid in node:
                    if has_modification_tag(kid):
                        self.tag(kid, 'm')
                
                if is_predication(node):
                    for kid in node:
                        if kid.tag.endswith('-SBJ'):
                            self.tag(kid, 'l') # TODO: is subject always left of predicate?
                        elif kid.tag == 'VP':
                            self.tag(kid, 'h')
                        elif kid.tag != 'PU':
                            self.tag(kid, 'a')
                    
                elif is_coordination(node): # coordination
                    for kid in node:
                        if kid.tag not in ('CC', 'PU'):
                            self.tag(kid, 'c')

                elif is_np_internal_structure(node):
                    first = True
                    for kid in reversed(node.kids):
                        if kid.tag not in ('CC', 'PU'):
                            if first:
                                self.tag(kid, 'N')
                                first = False
                            else:
                                self.tag(kid, 'n')

                elif is_internal_structure(node):
                    pass

                elif first_kid.is_leaf() or is_vp_internal_structure(first_kid): # head initial complementation
                    self.tag(first_kid, 'h')
                    for kid in node[1:node.count()]:
                        if self.is_postverbal_adjunct_tag(kid.tag):
                            self.tag(kid, 'a') # treat aspect particles as adjuncts
                        elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                            self.tag(kid, 'r')
                            
                # topicalisation WITH gap (NP-TPC-i)
                elif first_kid.tag.startswith('NP-TPC-'):
                    self.tag(first_kid, 't')
                    # really, we might want to tag the 'rest of phrase' as if the topicalised constituent
                    # weren't there
                    
                # topicalisation WITHOUT gap (NP-TPC)
                elif first_kid.tag.startswith('NP-TPC'):
                    self.tag(first_kid, 'T')

                # head final complementation
                elif (last_kid.is_leaf() or 
                      is_vp_internal_structure(last_kid) or
                      # lcp internal structure (cf 10:2(13)) is possible: despite the structure (LCP (NP) (LCP))
                      # this should be treated as head-final complementation, not adjunction.
                      is_lcp_internal_structure(last_kid)):
                    self.tag(last_kid, 'h')
                    
                    # cf 2:23(7), a number of derivations have (CP (WHNP-1 CP DEC)) instead of
                    # the expected (CP (WHNP-1) (CP DEC))
                    # This lets us treat what would otherwise be considered head-final as an
                    # adjunction
                    if last_kid.tag.startswith('DEC'):
                        for kid in node[0:node.count()-1]:
                            if kid.tag.startswith('WHNP'): self.tag(kid, 'a')
                            else: self.tag(kid, 'l')
                    else:
                        for kid in node[0:node.count()-1]:
                            if self.is_postverbal_adjunct_tag(kid.tag):
                                self.tag(kid, 'a') # treat aspect particles as adjuncts
                            elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                                self.tag(kid, 'l')

                elif is_apposition(node):
                    for kid in node:
                        if kid.tag.endswith('-APP'): #not kid.tag.startswith('PU'):
                            self.tag(kid, 'A')
                        else:
                            self.tag(kid, 'a')

                elif is_modification(node):
                    self.tag(last_kid, 'h')
                    
                    for kid in node[0:node.count()-1]:
                        if not kid.tag.endswith(':h'):
                            if has_modification_tag(kid):
                                self.tag(kid, 'm')
                            elif not kid.tag.startswith('PU'):
                                self.tag(kid, 'a')
                                
                            # XXX: this code is duplicated from above
                            # topicalisation WITH gap (NP-TPC-i)
                            elif kid.tag.startswith('NP-TPC-'):
                                self.tag(kid, 't')

                            # topicalisation WITHOUT gap (NP-TPC)
                            elif kid.tag.startswith('NP-TPC'):
                                self.tag(kid, 'T')

                else: # adjunction
                    self.tag(last_kid, 'h')

                    for kid in node[0:node.count()-1]:
#                        print kid.tag
#                        print kid.tag.startswith('NP-TPC')

                            
                        # XXX: this code is duplicated from above
                        # topicalisation WITH gap (NP-TPC-i)
                        if kid.tag.startswith('NP-TPC-'):
                            self.tag(kid, 't')

                        # topicalisation WITHOUT gap (NP-TPC)
                        elif kid.tag.startswith('NP-TPC'):
                            self.tag(kid, 'T')
                            
                        elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                            self.tag(kid, 'a')

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
        
