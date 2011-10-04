# coding: utf-8
from __future__ import with_statement
import os, re

from munge.proc.filter import Filter
from munge.trees.traverse import nodes, leaves
from munge.util.tgrep_utils import get_first
from munge.penn.nodes import Node

from munge.util.dict_utils import sorted_by_value_desc
from munge.util.list_utils import first_index_such_that, last_index_such_that
from munge.util.func_utils import satisfies_all

from apps.identify_lrhca import last_nonpunct_kid, get_nonpunct_kid, get_nonpunct_element
from apps.identify_pos import VerbalCategories, NominalCategories, has_question_tag
from apps.cn.fix_utils import inherit_tag, inherit_tag_str, replace_kid, base_tag, has_tag, has_tags
from apps.util.echo import echo
from apps.cn.output import OutputPrefacedPTBDerivation
from apps.util.config import config

PredicationRegex = re.compile(r'''
    (?:[:\w-]+)?
    (\s+[:\w-]+\s*)* # adjuncts (allow dashes and colons too, topicalised constituents already have :t/T)
    (?:(PU|FLR)\s+)* # 7:74(10)
    # allow dashes in the subject tag -- sometimes there are indices in the tag (NP-1)
    (?:[\w-]+-(?:PN|SBJ|APP)(?:-\d+)?|NP)\s+ # grammatical subject. IP < NP-PN VP occurs in 0:40(5), and an index may also be attached (2:68(3)). NP-APP VP occurs in 11:31(88)
    (?:(PU|FLR)\s+)* # FLR between NP and VP (20:8(7)). permit multiple PU/FLR in this position (26:84(7))
    VP # predicate
''', re.VERBOSE)
#(?:[:\w-]+)?\s*(\s+[:\w-]+\s*)*\s*(?:(PU|FLR)\s+)?\s*(?:[\w-]+-(?:PN|SBJ|APP)(?:-\d+)?|NP)\s+\s*(?:(PU|FLR)\s+)?\s*VP
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

def _has_modification_tag(node):
    if node.tag.startswith('CP'): return False # CP-m to be treated not as modification but adjunction

    last_dash_index = node.tag.rfind('-')
    return last_dash_index != -1 and node.tag[last_dash_index+1:] in FunctionTags
    
if config.modification_unary_rules:
    has_modification_tag = _has_modification_tag
else:
    def has_modification_tag(node):
        return False
    
# coordination is
# (PU spaces)+ (conjunct)( (PU spaces) conjunct)+ (final punctuation)*
# \b ensures that an entire conjunct is matched (we had a case where PP-PRP PU PP ADVP VP was unexpectedly matching)
# ETC gets pre-tagged as ETC:&, so we match against that
# TODO: 22:61(1) has NP(NP-APP PU NP-PN) mistagged as coordination
CoordinationRegex = re.compile(r'(?:(?:PU|CC) )*\b([\w:]+)(-[\w:-]+)?\b(?: (?:(?:PU|CC) )+\1(-[\w:-]+)?)+\s*(?: (?:PU|ETC(?::&)?))*$')

def tag_string_for_coordination(node):
    def _fix(tag):
        # Special case:
        # let IP and CP coordinate (SFP sentences are annotated CP)
        if tag in ('CP', 'CP-Q'): return 'IP'
        elif tag.startswith('SP') or tag.startswith('MSP'): return None # ignore SP (26:65(5))
        return tag

    # filter None, because kids to be ignored for the purpose of deciding coordination will map to None
    return ' '.join(filter(None, (_fix(kid.tag) for kid in node)))
    
_use_csc = config.use_csc
def is_coordination(node, at_top=False):
    global _use_csc

    if not any(kid.tag in ('CC', 'PU') for kid in node): return False
    match = CoordinationRegex.match(tag_string_for_coordination(node))

    if match and _use_csc:
        if at_top and all((kid.tag.startswith('IP') or kid.tag == 'PU') for kid in node) and not any(kid.tag == 'CC' for kid in node):
            for kid in node:
                if kid.tag == 'PU' and kid.lex in ('，', '；'):
                    kid.tag = 'CSC'
    return match
    
def is_ucp(node):
    return node.tag.startswith("UCP") and not (node[0].tag == "PU" and node[-1].tag == "PU")
    
def is_internal_structure(node):
    return all(kid.is_leaf() for kid in node)
    
ValidNPInternalTags = {'NN', 'NR', 'NT', 'JJ', 'PU', 'CC', 'ETC', 'ETC:&'}
def is_np_internal_structure(node):
    return node.tag.startswith('NP') and node.count() > 1 and (
        all(kid.tag in ValidNPInternalTags for kid in leaves(node)))
    
def is_vp_internal_structure(node):
    return node.count() > 1 and all(kid.tag in NominalCategories for kid in node)
    
def is_lcp_internal_structure(node):
    if not node.count() == 2: return False
    return node[0].tag == 'NP' and node[1].tag == 'LC'
    
def is_postverbal_adjunct_tag(tag):
    return tag.startswith('AS') or tag.startswith('DER')

def is_vpt(node):
    return node.tag[0:3] == 'VPT'

def is_vnv(node):
    return node.tag[0:3] == 'VNV'

def is_vcd(node):
    return node.tag[0:3] == 'VCD'

def is_vrd(node):
    return node.tag[0:3] == 'VRD'

def is_vcp(node):
    return node.tag[0:3] == 'VCP'

def is_vsb(node):
    return node.tag[0:3] == 'VSB'
    
VerbCompoundTags = {'VPT', 'VNV', 'VCD', 'VRD', 'VCP', 'VSB'}
def is_verb_compound(node):
    return node.tag[:3] in VerbCompoundTags
    
def is_prn(node):
    return node.tag.startswith('PRN') #and node[0].tag.startswith('PU')

def tag(kid, tag):
    '''Attaches a marker _tag_ to the given _kid_ node. If _kid_ is already tagged,
then no tag is attached.'''
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
    '''The CPTB annotation has some (possibly noisy) nodes which look like CCGbank-style right absorption: this returns True
for cases of this.'''
    return node.count() == 2 and base_tag(node.tag) == base_tag(node[0].tag) and node[1].tag == 'PU'
    
def is_repeated_unary_projection(tag, node):
    '''True if _node_ has _tag_, and the unary child of _node_ also has _tag_.'''
    return node.tag.startswith(tag) and node.count() == 1 and base_tag(node[0].tag) == tag and not node[0].is_leaf()
    
def leaf_kids(node):
    return filter(lambda e: e.is_leaf(), node)

def postprocess(root):
    use_lcp_to_np = config.lcp_to_np_typechange
    
    for node in nodes(root):
        # Exclude the conjuncts in LCP coordination: we want the LCP->NP promotion to apply once to the result of the coordination
#        if use_lcp_to_np and node.tag.startswith('LCP') and not (node.tag.endswith(':c') or node.tag.endswith(':h')):
        if use_lcp_to_np and node.tag.startswith('LCP') and has_tags(node, 'lr'):
            # if we're in LCP coordination then we want to protect the conjuncts from being converted
            new_node = Node('NP', [node])#, node.parent)
            inherit_tag(new_node, node)

            replace_kid(node.parent, node, new_node)
            
    return root
    
def preprocess(root):
    # IP < PP PU -> PP < PP PU (20:58(1))
    if root.count() == 2 and root[1].tag == 'PU' and root[0].tag.startswith('PP'): root.tag = root[0].tag
    
    for node in nodes(root):
        if node.is_leaf(): continue
                
        first_kid, first_kid_index = get_nonpunct_kid(node, get_last=False)
        last_kid,  last_kid_index  = get_nonpunct_kid(node, get_last=True)
        # ---------------------
        # Where LPU, RPU are paired punctuation, reshape YP(LPU ... XP RPU YP) into YP(XP(LPU ... XP) YP)
        if any(kid.lex in ("“", "「") for kid in leaf_kids(node)) and any(kid.lex in ("”", "」") for kid in leaf_kids(node)):
            lqu = first_index_such_that(lambda kid: kid.is_leaf() and kid.lex in ("“", "「"), node)
            rqu = first_index_such_that(lambda kid: kid.is_leaf() and kid.lex in ("”", "」"), node)
            if rqu != node.count()-1:
                quoted_kids = node.kids[lqu:rqu+1]
                del node.kids[lqu:rqu+1]

                last_nonpunct_kid, _ = get_nonpunct_element(quoted_kids, get_last=True)
                # Bad punctuation in 27:84(4) causes a mis-analysis, just ignore
                if last_nonpunct_kid:
                    quoted_node = Node(last_nonpunct_kid.tag, quoted_kids)
                    node.kids.insert(lqu, quoted_node)
        
        # CPTB/Chinese-specific fixes
        # ---------------------------
        # PP(P CP NP) in derivations like 5:11(3) should be PP(P NP(CP NP))
        if first_kid and first_kid.tag == "P" and node.count() > 2:
            last_tag = last_kid.tag
            rest = node.kids[1:]
            del node.kids[1:]
            node.kids.append(Node(last_tag, rest, node))
        # 2:12(3). DNP-PRD fixed by adding a layer of NP
        elif (node.tag.startswith('VP') and node.count() == 2 and 
                node[0].tag.startswith('VC') and 
                node[1].tag.startswith('DNP-PRD')): node[1] = Node('NP', [node[1]], node)
        # fix missing -OBJ tag from VP object complements (c.f. 31:18(4))
        elif (node.tag.startswith('VP') and node.count() >= 2 and
              node.tag.startswith('VP') and 
              node[0].tag == 'VV' and 
              node[-1].tag == 'NP'): node[-1].tag += "-OBJ"
        # fix bad annotation IP < IP (2:7(28)), VP < VP (0:1(5))
        elif any(is_repeated_unary_projection(xp, node) for xp in ('IP', 'VP', 'NP', 'CP')):
            node.kids = node[0].kids
        # treat DP-SBJ as QP-SBJ (6:37(9)): the rationale is that the determiner (e.g. 每) acts as a specifier,
        # just like a quantity
        elif node.tag == 'DP-SBJ':
            node.tag = 'QP-SBJ'
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
                
        elif node.tag.startswith('NP') and any(kid.tag.startswith('QP-APP') for kid in node):
            for kid in node:
                if kid.tag.startswith('QP-APP'): kid.tag = kid.tag.replace('QP', 'NP')
                
        # NP(CP NP-APP NP-PN) -> NP(CP NP(NP-APP NP-PN)) so that NP(NP-APP NP-PN) can receive NP internal structure-type analysis
        elif node.tag.startswith('NP') and node.count() == 3 and node[0].tag.startswith('CP') and node[1].tag.startswith('NP-APP') and node[2].tag.startswith('NP-PN'):
            np_app, np_pn = node[1], node[2]
            del node.kids[1:]
            
            node.kids.append(Node(node.tag, [np_app, np_pn], node))
                
        # IP < NP-SBJ ADVP VP rather than IP < NP-SBJ VP(ADVP VP) (25:59(12), 6:92(19))
        elif node.tag == 'IP' and node.count() == 3 and node[0].tag == 'NP-SBJ' and node[1].tag == 'ADVP' and node[2].tag == 'VP':
            advp = node.kids.pop(1)
            # VP is the new node[1]
            # now replace node[1] with Node(node[1])
            node[1] = Node(node[1].tag, [advp, node[1]], node)
            
        # fixing DNP(PN DEG), which causes mis-tagging DNP(PN:l DEG:h)
        # only 3 cases: 23:61(5), 9:14(14), 21:3(11)
        elif node.tag == 'DNP' and node.count() == 2 and node[0].tag == 'PN' and node[1].tag == 'DEG':
            replace_kid(node, node[0], Node('NP', [node[0]]))
            
        elif is_vnv(node) and node.count() == 3:
            # Re-analyse VNV as coordination
            node[1].tag = 'CC'
            
        # fix mistaggings of the form ADVP < JJ (1:7(9)), NP < JJ (5:35(1))
        elif node.count() == 1:
            if node[0].tag == 'JJ':
                if node.tag.startswith('ADVP'):
                    node.tag = node.tag.replace('ADVP', 'ADJP')
                elif node.tag.startswith('NP'):
                    node.tag = node.tag.replace('NP', 'ADJP')
            
            # fix NP < VV
            elif node.tag == 'NP' and node[0].tag == 'VV':
                node.tag = node.tag.replace('NP', 'VP')
                
            # fix NP < ADJP < JJ (5:35(1))
            elif node.tag == 'NP' and node[0].tag == 'ADJP':
                replace_kid(node.parent, node, node[0])
                
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
            elif node[0].tag == 'CP':
                if node.tag == 'NP-PRD':
                    node.kids = node[0].kids
                else:
                    # Rewrite NP < { CP < { CP < DEC } } 
                    # (i.e. 比 报告 的 早 一点) so that it's headed by the 的
                    expr = r'''/CP/ < { /CP/ < /DEC/ }'''
                    if get_first(node[0], expr):
                        node.kids = node[0].kids
                        
            elif node[0].tag in ('NP', 'NP-PN', 'VP', 'IP') and node.tag == 'PRN':
                node.kids = node[0].kids
                
            # ADVP < CS: shrink so that CS will be considered the head by binarise
            # CP < M: tagging error 7:14(8), 10:51(4), 11:13(32), 11:15(47)
            elif ((node.tag == 'ADVP' and node[0].tag == 'CS') or  
                  (node[0].tag == 'M' and node.tag == 'CP')):
                replace_kid(node.parent, node, node[0])
                
            # elif node.tag == 'VP' and node[0].tag == 'NP-PRD':
            #     replace_kid(node.parent, node, node[0])
            
            # couple of noisy derivs like 10:35(80), 10:26(121), 11:37(3)
            # elif node.tag == 'VP' and node[0].tag.startswith('IP'):
            #     replace_kid(node.parent, node, node[0])
                
        # Reshape LB (long bei)
        # ---------------------
        elif first_kid and first_kid.tag == "LB":            
            expr = r'''* < { /LB/=LB 
                       [ $ { * < /-(SBJ|OBJ|PN)/a=SBJ < /(V[PV]|VRD|VSB)/=PRED }
                       | $ { /CP/=CP < { *=IP < /-(SBJ|OBJ|PN)/a=SBJ < /(V[PV]|VRD|VSB)/=PRED } } ] }'''
            _, ctx = get_first(node, expr, with_context=True)
        
            lb, sbj, pred, cp, ip = ctx.lb, ctx.sbj, ctx.pred, ctx.cp, ctx.ip
            if cp:
                replace_kid(node, cp, ip)
        # 
        #     del node.kids
        #     node.kids = [lb, sbj, pred]
            
        # single mistagging CP-SBJ for CP in 24:58(1)
        elif node.tag == 'CP-SBJ': node.tag = 'CP'
        
        else:
            # Fix wrongly attached DEC (5:26(6))
            result = get_first(node, r'/CP/=TOP < { /IP/=P < { /NP/ $ /VP/ $ /DEC/=DEC } }', with_context=True)
            if result:
                _, ctx = result
                top, p, dec = ctx.top, ctx.p, ctx.dec
                
                top.kids.append(dec)
                p.kids.remove(dec)
                
            result = get_first(node, r'*=PP < { /IP-TPC/=P <1 { /NP/=T < ^/\*PRO\*/ } <2 /VP/=S }', nonrecursive=True, with_context=True)
            if result:
                _, ctx = result
                pp, p, s = ctx.pp, ctx.p, ctx.s
                inherit_tag(s, p)
                replace_kid(pp, p, s)
                
            expr = r'''/VP/=VP <1 /VV/=V <2 { /IP-OBJ/ <1 /NP-SBJ/=SBJ <2 /VP/=PRED }'''
            result = get_first(node, expr, with_context=True)
            if result:
                _, ctx = result
                vp, v, sbj, pred = ctx.vp, ctx.v, ctx.sbj, ctx.pred

                del vp.kids
                if get_first(sbj, r'* < ^/\*PRO\*/'):
                    vp.kids = [v, pred]
                else:
                    vp.kids = [v, sbj, pred]
                    
            expr = r'''/QP/=P <1 /CD/ <2 /CC/ <3 /CD/'''
            result = get_first(node, expr, with_context=True)
            if result:
                _, ctx = result
                p = ctx.p
                
                if p.count() <= 3: break
                
                cd_cc_cd, rest = p.kids[0:3], p.kids[3:]
                del p.kids[0:3]
                
                new_node = Node('QP', cd_cc_cd)
                p.kids.insert(0, new_node)
                
    return root
    
def is_argument_cluster(node):
    # Attested types of argument clusters are:
    # NP QP and NP IP (0:78(4))
    return (node.tag.startswith("VP") and node.count() == 2 
        and node[0].tag.startswith('NP') 
        # need to exclude NP QP-PRD (2:22(4))
        and (
            (node[1].tag.startswith('QP') and not node[1].tag.startswith('QP-PRD')) or
            (node[1].tag.startswith('IP'))))
            
def is_trace(node):
    return node.count() == 1 and node[0].tag == "-NONE-"

def label(root):
    root = preprocess(root)
    
    for node in nodes(root):
        if node.is_leaf(): continue
        
        at_top = False
        if node.parent is None: at_top = True
        
        first_kid, first_kid_index = get_nonpunct_kid(node, get_last=False)
        last_kid,  last_kid_index  = get_nonpunct_kid(node, get_last=True)
        
        for kid in node:
            if has_modification_tag(kid):
                tag(kid, 'm')
                
            elif kid.tag == 'MSP':
                tag(kid, 'a')
                
            elif kid.tag == 'FLR':
                tag(kid, 'a')
                
            elif kid.tag == 'ETC':
                tag(kid, '&')
                
            else:
                tag_if_topicalisation(kid)
                
        if is_prn(node):
            # PRN tagging error in 10:49(69)
            if not first_kid: continue
            
            node.tag = first_kid.tag
            tag(node, 'p')
            tag(node[0], 'h') # assume that the first PU introduces the PRN
            
        elif node.tag == 'FRAG':
            tag_adjunction(node, last_kid)
            
        # occasionally something that looks like CCG right absorption occurs in the original annotation (0:23(8))
        elif is_right_absorption(node):
            pass

        elif is_predication(node):
            sbj_assigned = False
            vp_assigned = False
            
            for kid in reversed(node):
                if not sbj_assigned and (kid.tag.rfind('-SBJ') != -1 or 
                    # TODO: we can get IP < NP-PN VP (0:40(5)). is this correct?
                    # exclude NP-PN-LOC (10:62(25))
                    (kid.tag.rfind('-PN') != -1 and kid.tag.rfind('-PN-LOC') == -1) or
                    # NP-APP VP in 11:31(88)
                    (kid.tag.rfind('-APP') != -1) or
                    kid.tag == "NP"):
                    
                    tag(kid, 'l') # TODO: is subject always left of predicate?
                    sbj_assigned = True
                elif not vp_assigned and kid.tag == 'VP':
                    tag(kid, 'h')
                    vp_assigned = True
                # elif _has_modification_tag(kid) and kid.tag.startswith('IP'):
                #     tag(kid, 'm')
                elif kid.tag not in ('PU', 'CC'):
                    tag(kid, 'a')
                    

            for i, kid in enumerate(node):
                try:
                    # exclude IP-SBJ PU VP from having the PU tagged :h (1:53(9))
                    if (kid.tag.startswith('IP-') or kid.tag.startswith('CP-')) and \
                       kid.tag.find('-TPC') == -1 and \
                       kid.tag.find('-SBJ') == -1 and \
                       node[i+1].tag == 'PU':
                        tag(node[i+1], 'h')
                        
                except: continue
                    
        elif node.count() == 1 and node.tag.startswith('VP') and is_verb_compound(node[0]):
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
                elif not kid.tag.startswith('PU'):
                    tag(kid, 'r')
                    
        elif is_vcd(node):
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
                elif not kid.tag.startswith('PU'):
                    tag(kid, 'r')

        elif is_coordination(node, at_top=at_top): # coordination
            for kid in node:
                if kid.tag == "ETC":
                    tag(kid, '&')

                if kid.tag not in ('CC', 'PU', 'CSC'):
                    tag(kid, 'c')
                                      
        elif is_np_internal_structure(node):
            first = True
            for kid in reversed(node.kids):
#                if kid.tag.startswith('PRN'): continue
                    
                if kid.tag == 'ETC':
                    tag(kid, '&')
                elif kid.tag not in ('CC', 'PU'):
                    if first:
                        tag(kid, 'N')
                        first = False
                    else:
                        tag(kid, 'n')
                else:
                    pass
                    
        # must be above is_coordination (it subsumes UCP)
        elif is_ucp(node):
            left_conjunct_tag = first_kid.tag
            # NOTE:
            # There are some cases where the UCP annotation is suspect (1:36(11))
            # we will obtain the wrong analysis in these cases because the UCP node
            # does not directly dominate its conjuncts
            
            old_tag = node.tag
            node.tag = left_conjunct_tag
            node.tag = inherit_tag_str(node.tag, old_tag)
            
            for kid in nodes(node):            
                if kid.tag is None:
                    print kid
                    print kid.tag
                
                if kid.tag.startswith('UCP'):
                    kid.tag = left_conjunct_tag
            for kid in node:
                if kid.tag == 'ETC':
                    tag(kid, '&')
                elif kid.tag not in ('CC', 'PU'):
                    tag(kid, 'C')

        # exclude VP < VV AS: we want to tag this
        elif (node.count() == 1) or is_verb_compound(node):
            pass

        elif ((first_kid.is_leaf() # head initial complementation
            # quoted verb (see fix in _preprocess_ function)
#           or all((kid.is_leaf() and kid.tag in ('PU', 'VV')) for kid in first_kid)
           or satisfies_all(
                lambda fkid: any(kid.is_leaf() and kid.tag == 'PU' for kid in fkid),
                lambda fkid: any(kid.is_leaf() and kid.tag == 'VV' for kid in fkid))(first_kid)
           or is_verb_compound(first_kid)
           # HACK: to fix weird case of unary PP < P causing adjunction analysis instead of head-initial
           # (because of PP IP configuration) in 10:76(4)
           or first_kid.tag == 'PP' and first_kid.count() == 1 and first_kid[0].tag == "P")):
           
            tag(first_kid, 'h')
            for kid in node[1:]:
                if is_postverbal_adjunct_tag(kid.tag) or kid.tag.startswith('ADVP'):
                    tag(kid, 'a') # treat aspect particles as adjuncts
                elif not kid.tag.startswith('PU'):
                    tag(kid, 'r')

        # head final complementation
        # This has to come after head initial complementation, otherwise we get the tagging VP < VV:l AS:h
        elif (last_kid.is_leaf() or 
              is_verb_compound(last_kid) or
              # lcp internal structure (cf 10:2(13)) is possible: despite the structure (LCP (NP) (LCP))
              # this should be treated as head-final complementation, not adjunction.
              is_lcp_internal_structure(last_kid)) and not any(first_kid.tag.find(ftag) != -1 for ftag in FunctionTags):
              
            if last_kid.tag.startswith('SP'): 
                # Treat final 吗 as the head to get the type-change category S[q]\S[dcl] (25:21(5))
                if has_question_tag(node):
                    tag(last_kid, 'h')
                else:
                    tag(last_kid, 'a')
                    
            else: tag(last_kid, 'h')

            # cf 2:23(7),1:9(28), a number of derivations have (CP(WHNP-1 CP(IP) DEC) XP) instead of
            # the expected (CP (WHNP-1) CP(IP DEC) XP)
            # This lets us treat what would otherwise be considered head-final as an
            # adjunction
            if last_kid.tag.startswith('DEC'):
                for kid in node[0:-1]:
                    if kid.tag.startswith('WHNP') or kid.tag.startswith('WHPP'): tag(kid, 'a')
                    elif not (kid.tag.startswith('PU') or
                        kid.tag.startswith('ADVP')): # ADVP as sibling of IP in 11:39(63)
                        tag(kid, 'l')
            else:
                for kid in node[0:-1]:
                    if (last_kid.tag in VerbalCategories and (
                            is_postverbal_adjunct_tag(kid.tag) or
                            # exception added to account for direct modification of V{V,A} with ADVP (0:47(9))
                            kid.tag.startswith('ADVP'))):
                        tag(kid, 'a') # treat aspect particles as adjuncts
                    elif not kid.tag.startswith('PU'):
                        tag(kid, 'l')

        # TODO: if this is below coordination, then NP(NP-APP PU NP) is considered coordination instead of apposition (10:70(15))
        #       actually, what happens if we get english-style apposition (NP1 , NP2)?
        elif is_apposition(node):
            if False:#any(kid.tag == 'IP-APP' for kid in node):
                tag(last_kid, 'h')
            else:
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
                if has_modification_tag(kid):
                    tag(kid, 'm')
                elif not kid.tag.startswith('PU'):
                    tag(kid, 'a')

                else:
                    tag_if_topicalisation(kid)
                        
        elif is_argument_cluster(node):
            for kid in node:
                tag(kid, '@')

        else: # adjunction
            tag_adjunction(node, last_kid)
    
    root = postprocess(root)
    
    return root
    
def tag_adjunction(node, last_kid):
    # noisy derivation 5:0(22)
    if not last_kid: return
    
    tag(last_kid, 'h')

    for kid in node[0:-1]:
        if kid.tag.endswith('-SBJ'): 
            # hack to handle predication nodes which fell through the PredicationRegex
            # because they had adjuncts attached at the wrong level between XP-SBJ and VP (11:13(89))
            tag(kid, 'l')
        elif not (kid.tag.startswith('PU') or kid.tag.startswith('CC')):
            tag(kid, 'a')
        else:
            tag_if_topicalisation(kid)

class TagStructures(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
                
    def accept_derivation(self, bundle):
        bundle.derivation = label(bundle.derivation)
        self.write_derivation(bundle)
            
    opt = '1'
    long_opt = 'tag'
    
    arg_names = 'OUTDIR'
