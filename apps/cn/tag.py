from __future__ import with_statement
import os, re

from munge.proc.filter import Filter
from munge.trees.traverse import nodes, leaves
from munge.util.dict_utils import sorted_by_value_desc

from apps.identify_pos import is_verb_compound
from apps.cn.output import OutputDerivation

from apps.util.config import config

def last_nonpunct_kid(node):
    kid, index = get_nonpunct_kid(node)
    return kid
    
def get_nonpunct_kid(node, get_last=True):
    if node.is_leaf(): return None, None
    
    if get_last:
        for i, kid in enumerate(reversed(node.kids)):
            if not kid.tag.startswith('PU'): return kid, node.count() - i - 1
    else:
        for i, kid in enumerate(node.kids):
            if not kid.tag.startswith('PU'): return kid, i
            
    return None, None

PredicationRegex = re.compile(r'''
    (?:[:\w-]+)?
    (\s+[:\w-]+\s*)* # adjuncts (allow dashes and colons too, topicalised constituents already have :t/T)
    # allow dashes in the subject tag -- sometimes there are indices in the tag (NP-1)
    [\w-]+-(?:PN|SBJ)\s+ # grammatical subject. IP < NP-PN VP occurs in 0:40(5)
    (?:PU\s+)?
    VP # predicate
''', re.VERBOSE)
def is_predication(node):
    kid_tags = ' '.join(kid.tag for kid in node)
    return node.tag.startswith('IP') and PredicationRegex.match(kid_tags)

def is_apposition(node):
    return (node.tag.startswith('NP') and 
        # exclude CP-APP? it's not really apposition, rather adjunction
        any(kid.tag != "CP-APP" and kid.tag.endswith('-APP') for kid in node))

# We exclude -IJ, so we can get analyses of INTJ nodes
FunctionTags = set('ADV TMP LOC DIR BNF CND DIR LGS MNR PRP'.split())

def is_modification(node):
    lnpk = last_nonpunct_kid(node)
    if not lnpk: return False
    
    if node.tag == lnpk.tag:
        return has_modification_tag(node[0])
    
    return False
    
ModificationRegex = re.compile(r'\w+-(\w+)')
def has_modification_tag(node):
    if not config.modification_unary_rules: return False
    
    if node.tag.startswith('CP'): return False # CP-m to be treated not as modification but adjunction
    
    last_dash_index = node.tag.rfind('-')
    return last_dash_index != -1 and node.tag[last_dash_index+1:] in FunctionTags
    
# coordination is
# (PU spaces)+ (conjunct)( (PU spaces) conjunct)+
# \b ensures that an entire conjunct is matched (we had a case where PP-PRP PU PP ADVP VP was unexpectedly matching)
CoordinationRegex = re.compile(r'(?:(?:PU|CC) )*\b([\w:]+)\b(?: (?:(?:PU|CC) )+\1)+')

def is_coordination(node):
    if not any(kid.tag in ('CC', 'PU') for kid in node): return False
    kid_tags = ' '.join(kid.tag for kid in node)
    return CoordinationRegex.match(kid_tags)
    
def is_internal_structure(node):
    return all(kid.is_leaf() for kid in node)
    
def is_np_internal_structure(node):
    return node.tag.startswith('NP') and node.count() > 1 and (
        all(kid.tag in ('NN', 'NR', 'NT', 'JJ', 'PU', 'CC', 'ETC') for kid in leaves(node)))
    
def is_vp_internal_structure(node):
    return node.count() > 1 and all(kid.tag in ('VV', 'VA', 'VC', 'VE') for kid in node)
    
def is_lcp_internal_structure(node):
    if not node.count() == 2: return False
    return node[0].tag == 'NP' and node[1].tag == 'LC'
    
def is_postverbal_adjunct_tag(tag):
    return tag.startswith('AS') or tag.startswith('DER')
    
def is_vpt(node):
    return node.tag.startswith('VPT')

def is_vnv(node):
    return node.tag.startswith('VNV')
    
def is_vcd(node):
    return node.tag.startswith('VCD')
    
def is_vrd(node):
    return node.tag.startswith('VRD')
    
def is_vcp(node):
    return node.tag.startswith('VCP')
    
def is_vsb(node):
    return node.tag.startswith('VSB')

def is_vp_compound(node):
    return any(f(node) for f in (is_vpt, is_vnv, is_vcd, is_vrd, is_vcp, is_vsb))

def tag(kid, tag):
    # make sure kid is not already tagged
    if len(kid.tag) >= 2 and kid.tag[-2] == ':': return

    kid.tag += (':' + tag)
    
if config.only_np_topicalisation_valid:
    def tag_if_topicalisation(node):
        # topicalisation WITH gap (NP-TPC-i)
        if node.tag.startswith('NP-TPC-'):
            tag(node, 't')

        # topicalisation WITHOUT gap (NP-TPC)
        elif node.tag.startswith('NP-TPC'):
            tag(node, 'T')
else:
    def tag_if_topicalisation(node):
        if node.tag.find('-TPC-') != -1: tag(node, 't')
        elif node.tag.find('-TPC') != -1: tag(node, 'T')

def label(root):
    for node in nodes(root):
        if not node.is_leaf():
            first_kid, first_kid_index = get_nonpunct_kid(node, get_last=False)
            last_kid,  last_kid_index  = get_nonpunct_kid(node, get_last=True)

            for kid in node:
                if has_modification_tag(kid):
                    tag(kid, 'm')
                    
                elif kid.tag in ('SP', 'MSP'):
                    tag(kid, 'a')
                    
                else:
                    tag_if_topicalisation(kid)

            if is_predication(node):
                for kid in node:
                    # TODO: we can get IP < NP-PN VP (0:40(5)). is this correct?
                    if kid.tag.endswith('-SBJ') or kid.tag.endswith('-PN'):
                        tag(kid, 'l') # TODO: is subject always left of predicate?
                    elif kid.tag == 'VP':
                        tag(kid, 'h')
                    elif kid.tag != 'PU':
                        tag(kid, 'a')
                        
            # elif is_parenthetical(node):

            elif is_np_internal_structure(node):
                first = True
                for kid in reversed(list(leaves(node))):
                    if kid.tag == 'ETC':
                        tag(kid, '&')
                    elif kid.tag not in ('CC', 'PU'):
                        if first:
                            tag(kid, 'N')
                            first = False
                        else:
                            tag(kid, 'n')
                    else:
                        # if tag is CC or PU, we want the previous
                        # tag to be N, not n
                        first = True
                        
            elif node.count() == 1 and node.tag.startswith('VP') and is_vp_compound(node[0]):
                pass
                        
            elif is_vpt(node): # fen de kai, da bu ying. vpt is head-final
                # tag(last_kid, 'h')
                # for kid in node[0:node.count()-1]:
                #     if kid.tag.startswith('AD'): tag(kid, 'h')
                #     elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                #         tag(kid, 'l')
                left = True
                for kid in node:
                    if kid.tag.startswith("AD") or kid.tag.startswith("DER"):
                        tag(kid, 'h')
                        left = False
                    elif left: 
                        tag(kid, 'l')
                    else:
                        tag(kid, 'r')
                        
            elif is_vsb(node):
                # tag(last_kid, 'h')
                # for kid in node[0:node.count()-1]:
                #     if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                #         tag(kid, 'a') # treat aspect particles as adjuncts
                #     elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                #         tag(kid, 'l')
                tag(first_kid, 'h')
                for kid in node[1:node.count()]:
                    if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                        tag(kid, 'a') # treat aspect particles as adjuncts
                    elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                        tag(kid, 'r')
                        
            elif is_vcd(node) or is_vnv(node):
                pass
                        
            elif is_vrd(node) or is_vcp(node) or is_vsb(node): # vrd is head-initial
                tag(first_kid, 'h')
                for kid in node[1:node.count()]:
                    if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                        tag(kid, 'a') # treat aspect particles as adjuncts
                    elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                        tag(kid, 'r')
            elif is_internal_structure(node) or is_verb_compound(node):
                pass

            elif is_coordination(node): # coordination
                for kid in node:
                    # TODO: putting ADVP in here stops misanalysis of 1:4(11), but what if we actually
                    # want coordination of adverbs?
                    if kid.tag not in ('CC', 'PU', 'ADVP'):
                        tag(kid, 'c')
                        
            elif ((first_kid.is_leaf() # head initial complementation
#               or is_vp_internal_structure(first_kid) 
                or is_vp_compound(first_kid)
               # HACK: to fix weird case of unary PP < P causing adjunction analysis instead of head-initial
               # (because of PP IP configuration) in 10:76(4)
               or first_kid.tag == 'PP' and first_kid.count() == 1 and first_kid[0].tag == "P")):
               # QP is headed by M
               # and not first_kid.tag in ("OD", "CD")):
                tag(first_kid, 'h')
                for kid in node[1:node.count()]:
                    if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                        tag(kid, 'a') # treat aspect particles as adjuncts
                    elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                        tag(kid, 'r')

            # # topicalisation WITH gap (NP-TPC-i)
            # elif first_kid.tag.startswith('NP-TPC-'):
            #     tag(first_kid, 't')
            #     # really, we might want to tag the 'rest of phrase' as if the topicalised constituent
            #     # weren't there
            # 
            # # topicalisation WITHOUT gap (NP-TPC)
            # elif first_kid.tag.startswith('NP-TPC'):
            #     tag(first_kid, 'T')

            # head final complementation
            elif (last_kid.is_leaf() or 
                  #last_kid.tag == "CLP" or
                  is_vp_compound(last_kid) or
#                  is_vp_internal_structure(last_kid) or
                  # lcp internal structure (cf 10:2(13)) is possible: despite the structure (LCP (NP) (LCP))
                  # this should be treated as head-final complementation, not adjunction.
                  is_lcp_internal_structure(last_kid)):
                  
                tag(last_kid, 'h')

                # cf 2:23(7),1:9(28), a number of derivations have (CP(WHNP-1 CP(IP) DEC) XP) instead of
                # the expected (CP (WHNP-1) CP(IP DEC) XP)
                # This lets us treat what would otherwise be considered head-final as an
                # adjunction
                if last_kid.tag.startswith('DEC'):
                    for kid in node[0:node.count()-1]:
                        if kid.tag.startswith('WHNP'): tag(kid, 'a')
                        elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h') or
                            kid.tag.startswith('ADVP')): # ADVP as sibling of IP in 11:39(63)
                            tag(kid, 'l')
                else:
                    for kid in node[0:node.count()-1]:
                        if (is_postverbal_adjunct_tag(kid.tag) or
                            # exception added to account for direct modification of V{V,A} with ADVP (0:47(9))
                            kid.tag.startswith('ADVP')):
                            tag(kid, 'a') # treat aspect particles as adjuncts
                        elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                            tag(kid, 'l')

            elif is_apposition(node):
                tag(last_kid, 'r') # HACK: assume apposition is right-headed

                for kid in node:
                    if not kid.tag.startswith('PU'):
                        # exclude CP-APP (see is_apposition() above)
                        if kid.tag.endswith('-APP') and not kid.tag.startswith('CP'):
                            tag(kid, 'A')
                        else:
                            tag(kid, 'a')

            elif is_modification(node):
                tag(last_kid, 'h')

                for kid in node[0:node.count()-1]:
                    if not kid.tag.endswith(':h'):
                        if has_modification_tag(kid):
                            tag(kid, 'm')
                        elif not kid.tag.startswith('PU'):
                            tag(kid, 'a')

                        else:
                            tag_if_topicalisation(kid)

            else: # adjunction
                tag(last_kid, 'h')

                for kid in node[0:node.count()-1]:
                    if not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                        tag(kid, 'a')
                    else:
                        tag_if_topicalisation(kid)
    return root
    
class TagStructures(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self)
        self.outdir = outdir
                
    def accept_derivation(self, bundle):
        bundle.derivation = label(bundle.derivation)
        self.write_derivation(bundle)
            
    opt = '1'
    long_opt = 'tag'
    
    arg_names = 'OUTDIR'
