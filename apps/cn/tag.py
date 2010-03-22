from __future__ import with_statement
import os, re

from munge.proc.filter import Filter
from munge.trees.traverse import nodes, leaves
from munge.util.dict_utils import sorted_by_value_desc
from apps.identify_lrhca import base_tag, last_nonpunct_kid, get_nonpunct_kid
from apps.cn.fix_utils import inherit_tag

from apps.identify_pos import is_verb_compound
from apps.cn.output import OutputDerivation

from apps.util.config import config

PredicationRegex = re.compile(r'''
    (?:[:\w-]+)?
    (\s+[:\w-]+\s*)* # adjuncts (allow dashes and colons too, topicalised constituents already have :t/T)
    # allow dashes in the subject tag -- sometimes there are indices in the tag (NP-1)
    (?:[\w-]+-(?:PN|SBJ)(?:-\d+)?|NP)\s+ # grammatical subject. IP < NP-PN VP occurs in 0:40(5), and an index may also be attached (2:68(3))
    (?:(PU|FLR)\s+)? # FLR between NP and VP (20:8(7))
    VP # predicate
''', re.VERBOSE)
def is_predication(node):
    kid_tags = ' '.join(kid.tag for kid in node)
    return node.tag.startswith('IP') and PredicationRegex.match(kid_tags)

def is_apposition(node):
    # QP < NP-APP QP in 0:8(7)
    return ((node.tag.startswith('NP') or node.tag.startswith('QP')) and 
        # exclude CP-APP? it's not really apposition, rather adjunction
        any(kid.tag != "CP-APP" and kid.tag.endswith('-APP') for kid in node))

# We exclude -IJ, so we can get analyses of INTJ nodes
FunctionTags = frozenset('ADV TMP LOC DIR BNF CND DIR LGS MNR PRP'.split())

def is_modification(node):
    lnpk = last_nonpunct_kid(node)
    if not lnpk: return False
    
    if node.tag == lnpk.tag:
        return has_modification_tag(node[0])
    
    return False

if config.modification_unary_rules:
    def has_modification_tag(node):
        if node.tag.startswith('CP'): return False # CP-m to be treated not as modification but adjunction
    
        last_dash_index = node.tag.rfind('-')
        return last_dash_index != -1 and node.tag[last_dash_index+1:] in FunctionTags
else:
    def has_modification_tag(node):
        return False
    
# coordination is
# (PU spaces)+ (conjunct)( (PU spaces) conjunct)+ (final punctuation)*
# \b ensures that an entire conjunct is matched (we had a case where PP-PRP PU PP ADVP VP was unexpectedly matching)
#CoordinationRegex = re.compile(r'(?:(?:PU|CC) )*\b([\w:]+)\b(?: (?:(?:PU|CC) )+\1)+\s*(?: PU)*$')
CoordinationRegex = re.compile(r'(?:(?:PU|CC) )*\b([\w:]+)(-[\w:-]+)?\b(?: (?:(?:PU|CC) )+\1(-[\w:-]+)?)+\s*(?: (?:PU|ETC))*$')
# Below regex accounts for coordination when POS tags differ by CPTB tag (eg IP-OBJ PU IP PU IP): is 29:99(14) just a tagging error?
#CoordinationRegex = re.compile(r'(?:(?:PU|CC) )*\b([\w:]+)[\w:-]+\b(?: (?:(?:PU|CC) )+\1(-[\w:-]+)?)+')

def is_coordination(node):
    def _fix(tag):
        if tag in ('CP', 'CP-Q'): return 'IP'
        return tag
        
    if not any(kid.tag in ('CC', 'PU') for kid in node): return False
    # Special case:
    # let IP and CP coordinate (SFP sentences are annotated CP)
    kid_tags = ' '.join(_fix(kid.tag) for kid in node)
    return CoordinationRegex.match(kid_tags)
    
def is_ucp(node):
    return node.tag.startswith("UCP") and not (node[0].tag == "PU" and node[-1].tag == "PU")
    
def is_internal_structure(node):
    return all(kid.is_leaf() for kid in node)
    
ValidNPInternalTags = frozenset(('NN', 'NR', 'NT', 'JJ', 'PU', 'CC', 'ETC'))
def is_np_internal_structure(node):
    return node.tag.startswith('NP') and node.count() > 1 and (
        all(kid.tag in ValidNPInternalTags for kid in leaves(node)))
    
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
    
def is_prn(node):
    return node.tag.startswith('PRN') and node[0].tag.startswith('PU')

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
        # PP-TPC (7:4(5)) should not result in a unary rule PP -> S/S
        if node.tag == 'PP-TPC': return
        
        if node.tag.find('-TPC-') != -1: tag(node, 't')
        elif node.tag.find('-TPC') != -1: tag(node, 'T')
        
def is_right_absorption(node):
    return node.count() == 2 and base_tag(node.tag) == base_tag(node[0].tag) and node[1].tag == 'PU'
    
def is_repeated_unary_projection(tag, node):
    return node.tag.startswith(tag) and node.count() == 1 and base_tag(node[0].tag) == tag and not node[0].is_leaf()
    
def preprocess(root):
    # IP < PP PU -> PP < PP PU (20:58(1))
    if root.count() == 2 and root[1].tag == 'PU' and root[0].tag.startswith('PP'): root.tag = root[0].tag
    
    for node in nodes(root):
        if node.is_leaf(): continue
        
        first_kid, first_kid_index = get_nonpunct_kid(node, get_last=False)
        last_kid,  last_kid_index  = get_nonpunct_kid(node, get_last=True)
        
        # CPTB/Chinese-specific fixes
        # ---------------------------
        # PP(P CP NP) in derivations like 5:11(3) should be PP(P NP(CP NP))
        if first_kid and first_kid.tag == "P" and node.count() > 2:
            last_tag = last_kid.tag
            rest = node.kids[1:]
            del node.kids[1:]
            node.kids.append(Node(last_tag, rest, node))
        # 2:12(3). DNP-PRD fixed by adding a layer of NP
        elif node.tag.startswith('VP') and node.count() == 2 and node[0].tag.startswith('VC') and node[1].tag.startswith('DNP-PRD'):
            node[1] = Node('NP', [node[1]], node)
        # fix missing -OBJ tag from VP object complements (c.f. 31:18(4))
        elif node.tag.startswith('VP') and node.count() >= 2 and node[0].tag == 'VV' and node[-1].tag == 'NP':
            node[-1].tag += "-OBJ"
        # fix bad annotation IP < IP (2:7(28)), VP < VP (0:1(5))
        elif any(is_repeated_unary_projection(xp, node) for xp in ('IP', 'VP', 'NP')):
            node.kids = node[0].kids
        # attach the PU preceding a PRN under the PRN
        elif last_kid and last_kid.tag == 'PRN' and last_kid.count() == 1:
            maybe_pu = node[last_kid_index-1]
            if maybe_pu.tag == 'PU':
                del node.kids[last_kid_index-1]
                last_kid.kids.insert(0, maybe_pu) # prepend
        # DEG instead of DEC (29:34(3)). if there's a trace in DEG's sibling and no DEC, then change DEG to DEC.
        elif node.tag == 'CP' and node.count() == 2 and node[0].tag == 'IP' and node[1].tag == 'DEG':
            if get_first(node[0], r'^/\*T\*/') and not get_first(node[0], r'/DEC/'):
                node[1].tag = 'DEC'
            
        # fix mistaggings of the form ADVP < JJ (1:7(9)), NP < JJ (5:35(1))
        elif node.count() == 1:
            if node[0].tag == 'JJ':
                if node.tag.startswith('ADVP'):
                    node.tag = node.tag.replace('ADVP', 'ADJP')
                elif node.tag.startswith('NP'):
                    node.tag = node.tag.replace('NP', 'ADJP')
            # fix projections NP < QP
            elif node[0].tag.startswith('QP') and node.tag.startswith('NP'):
                inherit_tag(node[0], node) # copy PCTB tags from NP to QP
                node.tag = node[0].tag # copy QP to parent, replacing NP
                node.kids = node[0].kids
            elif node[0].tag == 'IP' and node.tag == 'CP-APP':
                inherit_tag(node[0], node)
                node.tag = node[0].tag
                node.kids = node[0].kids
            # CLP < NN
            elif node[0].tag == 'NN' and node.tag == 'CLP':
                node[0].tag = 'M'
            elif node[0].tag == 'NN' and node.tag.startswith("VP"):
                node[0].tag = 'VV'
                
    return root

from munge.util.tgrep_utils import get_first
from munge.penn.nodes import Node
def label(root):
    root = preprocess(root)
    
    for node in nodes(root):
        if node.is_leaf(): continue
        
        first_kid, first_kid_index = get_nonpunct_kid(node, get_last=False)
        last_kid,  last_kid_index  = get_nonpunct_kid(node, get_last=True)
        
        # Reshape LB (long bei)
        # ---------------------
        if first_kid and first_kid.tag == "LB":
            expr = r'''* < { /LB/=LB [ $ { * < /-(SBJ|OBJ|PN)/a=SBJ < /(V[PV]|VRD|VSB)/=PRED }
                       | $ { /CP/ < { * < /-(SBJ|OBJ|PN)/a=SBJ < /(V[PV]|VRD|VSB)/=PRED } }  ] }'''
            _, ctx = get_first(node, expr, with_context=True)
            
            lb = ctx['LB']
            sbj, pred = ctx['SBJ'], ctx['PRED']
            
            del node.kids
            node.kids = [lb, sbj, pred]
            
        # ---------------------
        
        for kid in node:
            if has_modification_tag(kid):
                tag(kid, 'm')
                
            elif kid.tag in ('SP', 'MSP'):
                tag(kid, 'a')
            #     
            # elif is_prn(kid):
            #     # PRN tagging error in 10:49(69)
            #     if not first_kid: continue
            # 
            #     node.tag = first_kid.tag
            #     tag(node, 'p')
            #     tag(node[0], 'h') # assume that the first PU introduces the PRN
                
            else:
                tag_if_topicalisation(kid)
                
        if is_prn(node):
            # PRN tagging error in 10:49(69)
            if not first_kid: continue
            
            node.tag = first_kid.tag
            tag(node, 'p')
            tag(node[0], 'h') # assume that the first PU introduces the PRN
            
        # occasionally something that looks like CCG right absorption occurs in the original annotation (0:23(8))
        elif is_right_absorption(node):
            pass

        elif is_predication(node):
            for kid in node:
                # TODO: we can get IP < NP-PN VP (0:40(5)). is this correct?
                if kid.tag.rfind('-SBJ') != -1 or kid.tag.rfind('-PN') != -1 or kid.tag == "NP":
                    tag(kid, 'l') # TODO: is subject always left of predicate?
                elif kid.tag == 'VP':
                    tag(kid, 'h')
                elif kid.tag not in ('PU', 'CC'):
                    tag(kid, 'a')
                    
        elif node.count() == 1 and node.tag.startswith('VP') and is_vp_compound(node[0]):
            pass
                    
        elif is_vpt(node): # fen de kai, da bu ying. vpt is head-final
            left = True
            for kid in node:
                if kid.tag.startswith("AD") or kid.tag.startswith("DER"):
                    tag(kid, 'h')
                    left = False
                elif left: 
                    tag(kid, 'l')
                else:
                    tag(kid, 'r')
                    
        elif is_vsb(node): # VSB is modifier+head, and hence is head-final
            tag(first_kid, 'h')
            for kid in node[1:]:
                if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                    tag(kid, 'a') # treat aspect particles as adjuncts
                elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                    tag(kid, 'r')
                    
        elif is_vcd(node) or is_vnv(node):
            pass
            
        elif is_vcp(node):
            tag(first_kid, 'h')
            for kid in node[1:]:
                if kid.tag == "VC":
                    tag(kid, 'a')
                    
        elif is_vrd(node) or is_vsb(node): # vrd is head-initial
            tag(first_kid, 'h')
            for kid in node[1:]:
                if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                    tag(kid, 'a') # treat aspect particles as adjuncts
                elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                    tag(kid, 'r')

        elif is_coordination(node): # coordination
            for kid in node:
                if kid.tag == "ETC":
                    tag(kid, '&')

                if kid.tag not in ('CC', 'PU'):
                    tag(kid, 'c')
                    
        elif is_np_internal_structure(node):
            first = True
            for kid in reversed(node.kids):
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
#                    first = True
                    pass
                    
        # must be above is_coordination (it subsumes UCP)
        elif is_ucp(node):
            left_conjunct_tag = first_kid.tag
            node.tag = left_conjunct_tag
            for kid in nodes(node):
                if kid.tag.startswith('UCP'):
                    kid.tag = left_conjunct_tag
            for kid in node:
                if kid.tag == 'ETC':
                    tag(kid, '&')
                elif kid.tag not in ('CC', 'PU'):
                    tag(kid, 'C')

        elif is_internal_structure(node) or is_verb_compound(node):
            pass

        elif ((first_kid.is_leaf() # head initial complementation
#               or is_vp_internal_structure(first_kid) 
            or is_vp_compound(first_kid)
           # HACK: to fix weird case of unary PP < P causing adjunction analysis instead of head-initial
           # (because of PP IP configuration) in 10:76(4)
           or first_kid.tag == 'PP' and first_kid.count() == 1 and first_kid[0].tag == "P")):
           
            tag(first_kid, 'h')
            for kid in node[1:]:
                if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                    tag(kid, 'a') # treat aspect particles as adjuncts
                elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h')):
                    tag(kid, 'r')

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
                for kid in node[0:-1]:
                    if kid.tag.startswith('WHNP') or kid.tag.startswith('WHPP'): tag(kid, 'a')
                    elif not (kid.tag.startswith('PU') or kid.tag.endswith(':h') or
                        kid.tag.startswith('ADVP')): # ADVP as sibling of IP in 11:39(63)
                        tag(kid, 'l')
            else:
                for kid in node[0:-1]:
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

            for kid in node[0:-1]:
                if not kid.tag.endswith(':h'):
                    if has_modification_tag(kid):
                        tag(kid, 'm')
                    elif not kid.tag.startswith('PU'):
                        tag(kid, 'a')

                    else:
                        tag_if_topicalisation(kid)

        else: # adjunction
            tag(last_kid, 'h')

            for kid in node[0:-1]:
                if not (kid.tag.startswith('PU') or kid.tag.startswith('CC') or kid.tag.endswith(':h')):
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
