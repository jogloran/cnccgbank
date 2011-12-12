# coding=utf-8
from copy import copy

from apps.cn.catlab import ptb_to_cat

from apps.util.echo import echo

from munge.proc.tgrep.tgrep import tgrep, find_first, find_all
from munge.penn.aug_nodes import Node

from munge.trees.pprint import pprint
from munge.util.tgrep_utils import get_first
from munge.cats.cat_defs import *
from munge.cats.trace import analyse
from munge.cats.nodes import FORWARD, BACKWARD
from munge.trees.traverse import lrp_repr

from munge.util.err_utils import warn, debug
from munge.util.dict_utils import update

from apps.cn.fix import Fix
from apps.cn.fix_utils import *

def get_trace_index_from_tag(tag):
    bits = base_tag(tag, strip_cptb_tag=False).rsplit('-', 1)
    if len(bits) != 2:
        return ""
    else:
        return "-" + bits[1]
        
def is_rooted_in(subcat, cat, respecting_features=False):
    cur = cat
    while not cur.is_leaf() and cur.left:
        cur = cur.left
    return cur.equal_respecting_features(subcat) if respecting_features else cur == subcat
    
use_bare_N = config.use_bare_N
    
ModifierTags = frozenset(("TPC", "LOC", "EXT", "ADV", "DIR", "IO", "LGS", "MNR", "PN", "PRP", "TMP", "TTL"))
ModifierTagsRegex = "(?:" + "|".join(ModifierTags) + ")"
class FixExtraction(Fix):
    def pattern(self):
        return list((
            # must come before object extraction
#            (r'*=TOP $ /-SBJ-d+/a=N < { * < /LB/=BEI } << { /NP-(?:TPC|OBJ)/ < ^/\*/ $ /V[PV]|VRD|VSB|VCD/=PRED }', self.fix_reduced_long_bei_gap),
#            (r'*=TOP                < { * < /LB/=BEI } << { /NP-(?:TPC|OBJ)/ < ^/\*/ $ /V[PV]|VRD|VSB|VCD/=PRED }', self.fix_reduced_long_bei_gap),
            (r'*=TOP < { /LB/=BEI $ { /IP/=S < { /VP/=VP < /V[PV]|VRD|VSB|VCD/=PRED < { /NP-OBJ/ < ^/\*/ } } }=BEIS }', self.fix_lb),
            
            # doesn't work for 1:34(8) where an additional PP adjunct intervenes
            (r'*=TOP < { /PP-LGS/ < /P/=BEI } << { /NP-(?:TPC|OBJ)/ < ^/\*/ $ /V[PV]|VRD|VSB|VCD/=PRED }', self.fix_reduced_long_bei_gap),

            (r'/SB/=BEI $ { *=PP < { *=P < { /NP-SBJ/=T < ^/\*-\d+$/ $ *=S } } }', self.fix_short_bei_subj_gap), #0:11(4)
            # QP-OBJ in 8:64(10) (good example)
            (r'{ /SB/=BEI $ { /VP/=BEIS <<    { /[NQ]P-OBJ/=T < ^/\*-\d+$/ $ *=S > { *=P > *=PP } } } }', self.fix_short_bei_obj_gap), #1:54(3)
            (r'{ /SB/=BEI $ { /VP/=BEIS << { /VP/=P < { /NP-IO/=T < ^/\*-\d+$/ $ *=S } > *=PP } } }', self.fix_short_bei_io_gap), # 31:2(3)

            (r'/VP/=P < {/-TPC-\d+:t$/a=T $ /VP/=S }', self.fix_whword_topicalisation),
            # TODO: needs to be tested with (!NP)-TPC
            (r'/(IP|CP-CND)/=P < {/-TPC-\d+:t$/a=T $ /(IP|CP-CND)/=S }', self.fix_topicalisation_with_gap),
            # if config.vp_nongap_topicalisation is set, this adds the unary rule NP -> VP/VP (10:6(36))
            # otherwise, 10:6(36) actually gets an incorrect analysis
            (
                (r'/(IP|CP-CND|VP)/=P < {/-TPC:T$/a=T     $ /(IP|CP-CND|VP)/=S }', self.fix_topicalisation_without_gap)
                if config.vp_nongap_topicalisation else
                (r'/(IP|CP-CND)/=P < {/-TPC:T$/a=T     $ /(IP|CP-CND)/=S }', self.fix_topicalisation_without_gap)
            ),

            # Adds a unary rule when there is a clash between the modifier type (eg PP-PRD -> PP)
            # and what is expected (eg S/S)
            # This should come first, otherwise we get incorrect results in cases like 0:5(7).
            (r'*=P <1 {/:m$/a=T $ *=S}', self.fix_modification),

            # The node [CI]P will be CP for the normal relative clause construction (CP < IP DEC), and
            # IP for the null relativiser construction.
            # TODO: unary rule S[dcl]|NP -> N/N is only to apply in the null relativiser case.
            (r'^/\*RNR\*/ >> { * < /:c$/a }=G', self.fix_rnr),
            # an argument cluster is defined as a VP, one conjunct of which has a verb, and one which does not
            (r'''/VP/
                    < { /VP:c/=PP
                        <1 { /V[PVECA]|VRD|VSB|VCD/=P < { /NP/=S $ *=T } } 
                        <2 /(QP|V[PV])/ } 
                    < { /VP/ 
                        < { /(PU|CC)/ 
                      [ $ { /VP:c/ 
                            ! <1 /V[PVECA]|VRD|VSB|VCD/ 
                            <1 /NP/ 
                            <2 /(QP|V[PV])/ }
                      | $ { /VP/ <
                            { /VP:c/ 
                                    ! <1 /V[PVECA]|VRD|VSB|VCD/ 
                                    <1 /NP/ 
                                    <2 /(QP|V[PV])/ } } ] } }''', self.clusterfix),

            # A few derivations annotate the structure of 他是去年开始的 as VP(VC NP-PRD(CP))
            # Also, we permit NP to appear in PRED to get an analysis of NP(VP 的) as headed by the 的 (see the preprocessing case in tag.py)
            (r'^/\*T\*/ > { /NP-SBJ/ >> { /[CI]P/ $ /WHNP(-\d+)?/=W > { /(CP|NP|NP-PRD)/=PRED > *=N } } }', self.fix_subject_extraction),
            (r'^/\*T\*/ > { /NP-SBJ/ >>                               { /CP/=PRED > *=N } }', self.fix_reduced(self.fix_subject_extraction)),
            
            (r'^/\*T\*/ > { /NP-(OBJ|EXT)/ >> { /[CI]P/ $ /WHNP(-\d+)?/=W > { /(CP|NP|NP-PRD)/=PRED > *=N } } }', self.fix_object_extraction),
            (r'^/\*T\*/ > { /NP-OBJ/ >>                               { /CP/=PRED > *=N } }', self.fix_reduced(self.fix_object_extraction)),

            # [ICV]P is in the expression because, if a *PRO* subject gap exists and is removed by catlab, we will not find a full IP in that position but a VP
            (r'''^/\*T\*/ > { /[NPQ]P(?:-%(tags)s)?(?!-\d+)/=K 
                         >> { /[ICV]P/ $ {/WH[NP]P(-\d+)?/ > { /CP/=PRED > *=N } } } }'''
                         % { 'tags': ModifierTagsRegex }, self.fix_nongap_extraction),

           # (r'* < { /IP-APP/=A $ /N[NRT]/=S }', self.fix_ip_app),

            # ba-construction object gap
            (r'*=TOP < { /BA/=BA $ { * << ^/\*-/ }=C }', self.fix_ba_object_gap),

            # Removes the prodrop trace *pro*
            # Also removes control/raising traces *PRO* which we have chosen not to shrink in catlab
            # (see call to is_PRO_trace in label_root() of catlab.py)
            (r'*=PP < { *=P < ^/\*(pro|PRO)\*/ }', self.fix_prodrop),

            # Removes wayward WHNP traces without a coindex (e.g. 0:86(5), 11:9(9))
            (r'* < { * < /WHNP(?!-)/ }', self.remove_null_element),
            # Removes undischarged topicalisation traces
#            (r'*=PP < { *=P < { /-TPC/a=T << ^/\*T\*/ $ *=S } }', self.remove_tpc_trace),
#            (r'*=PP < { *=P < { { * < ^/\*-\d+/ }=T $ *=S } }', self.remove_tpc_trace),
            # Removes undischarged extraction traces (often associated with NP < WHNP CP(IP DEC), see 2:49(6))
            (r'*=PP < { *=P < { { /WHNP-/ < ^/\*OP\*/ }=T $ *=S } }', self.remove_tpc_trace)
        ))

    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix_lb(self, _, top, vp, pred, s, bei, beis):
        replace_kid(s, vp, pred)
        self.fix_categories_starting_from(pred, until=s)
        self.relabel_lb(bei, beis)
        
    def relabel_lb(self, bei, beis):
        bei.category = bei.category.clone_with(right=beis.category)
        
    def clusterfix(self, top, pp, p, s, t):
        debug("Fixing argument cluster coordination: %s", pprint(top))
        debug('T: %s', t)
        # 1. Shrink the verb (node T)
        self.fix_object_gap(pp, p, t, s)
        # 2. Reattach the verb above the TOP node
        new_node = Node('TAG', top.kids, top.category, head_index=0)
        top.kids = [t, new_node]
        # (Reattaching parent pointers)
        for kid in new_node: kid.parent = new_node
        
        # 3. Find and relabel argument clusters
        for node, ctx in find_all(top, r'/VP/=VP <1 /NP/=NP <2 /(QP|V[PV])/=QP', with_context=True):
            vp, np, qp = ctx.vp, ctx.np, ctx.qp
            # Now, VP should have category ((S[dcl]\NP)/QP)/NP
            SbNP = t.category.left.left
            QP, NP = qp.category, np.category
            # NP should have category ((S[dcl]\NP)/QP)\(((S[dcl]\NP)/QP)/NP)
            new_np_category = (SbNP/QP)|((SbNP/QP)/NP)
            # QP should have category ((S[dcl]\NP)\((S[dcl]\NP)/QP))
            new_qp_category = (SbNP)|((SbNP)/QP)

            # insert unary nodes
            new_np_node = Node(np.tag, [np], new_np_category, head_index=0); np.parent = new_np_node
            new_qp_node = Node(qp.tag, [qp], new_qp_category, head_index=0); qp.parent = new_qp_node

            replace_kid(vp, np, new_np_node)
            replace_kid(vp, qp, new_qp_node)
            
            self.fix_categories_starting_from(new_np_node, top)

    def remove_tpc_trace(self, _, pp, p, t, s):
        replace_kid(pp, p, s)

    def fix_rnr(self, rnr, g):
        # G is the node dominating all the conjuncts
        rnr_tags = []
        for node, ctx in find_all(
            g, r'/:c/a', with_context=True):
            for rnr in find_all(
                node, r'^/\*RNR\*/'):
                rnr_tags.append(get_trace_index_from_tag(rnr.lex))

        for index in rnr_tags:
            for node, ctx in find_all(
                g,
                r'*=PP < { *=P < { *=T < ^/\*RNR\*%s/ $ *=S } }' % index,
                with_context=True
            ):
                inherit_tag(ctx.s, ctx.p)
                self.fix_object_gap(ctx.pp, ctx.p, ctx.t, ctx.s)
                self.fix_categories_starting_from(ctx.s, g)
                
        last_conjunct = list(find_first(g, r'/:c/a', left_to_right=False))
        
        args = []
        for index in rnr_tags:
            # find_first, because we only want to find one match, the shallowest.
            # cf 7:27(10), if NP-OBJ-2(NN NP-OBJ-2(JJ NN)), then we only want to identify
            # one matching node for index -2 -- the shallowest -- and not two.
            for node, ctx in find_first(
                last_conjunct[0],
                r'*=P < { /%s/a=T $ *=S }' % index,
                with_context=True
            ):
                args.append(ctx.t)
                
                # Note: last_conjunct may be disconnected from
                # the tree by replace_kid (when ctx.p == last_conjunct)
                replace_kid(ctx.p.parent, ctx.p, ctx.s)
                self.fix_categories_starting_from(ctx.s, g)
                
        # Because the find_all which retrieved the args is an in-order left-to-right traversal, it will find
        # shallower nodes before deeper nodes. Therefore, if a verb has two args V A1 A2, the _args_ list will
        # contain [A2, A1] because A2 is shallower (further from the head) than A1.
        # We reverse the list of args, so that args are re-attached from the inside out (starting from A1).
        args.reverse()
        
        new_g = g
        for arg in args:
            new_g = Node(new_g.tag, [new_g, arg], new_g.category.left, head_index=0)
        
        replace_kid(g.parent, g, new_g)
                
    def fix_short_bei_subj_gap(self, node, bei, pp, p, t, s):
        debug("fixing short bei subject gap: %s", lrp_repr(pp))
        # take the VP sibling of SB
        # replace T with S
        # this analysis isn't entirely correct
        replace_kid(pp, p, s)
        self.fix_categories_starting_from(s, pp)
        bei.category = bei.category.clone_with(right=bei.parent[1].category)

    def fix_short_bei_obj_gap(self, node, pp, bei, beis, t, p, s):
        debug("fixing short bei object gap: pp:%s\np:%s\ns:%s", lrp_repr(pp), lrp_repr(p), lrp_repr(s))
        
        # simple test case in 29:71(3) for bei with extracted NP
        replace_kid(pp, p, s)
        self.fix_categories_starting_from(s, until=bei.parent[1])
        bei.category = bei.category.clone_with(right=bei.parent[1].category)
        
    def fix_short_bei_io_gap(self, node, pp, bei, beis, t, p, s):
        debug("fixing short bei io gap: pp:%s\np:%s\ns:%s", lrp_repr(pp), lrp_repr(p), lrp_repr(s))
        
        replace_kid(pp, p, s)
        self.fix_categories_starting_from(s, until=pp)
        bei.category = bei.category.clone_with(right=beis.category)

    def remove_null_element(self, node):
        # Remove the null element WHNP and its trace -NONE- '*OP*' and shrink tree
        pp, ctx = get_first(node, r'*=PP < { *=P < { /WH[NP]P/=T $ *=S } }', with_context=True)
        p, t, s = ctx.p, ctx.t, ctx.s

        replace_kid(pp, p, s)

    def relabel_relativiser(self, node):
        # Relabel the relativiser category (NP/NP)\S to (NP/NP)\(S|NP)
        
        result = get_first(node, r'*=S $ /(DEC|SP)/=REL', with_context=True, left_to_right=True)

        if result is not None:
            _, context = result
            s, relativiser = context.s, context.rel

            relativiser.category = relativiser.category.clone_with(right=s.category)
            debug("New rel category: %s", relativiser.category)

            return True
        else:
            warn("Couldn't find relativiser under %s", node)
            return False

    @staticmethod
    def is_topicalisation(cat):
        # T/(T/X)
        return (cat.is_complex() and cat.right.is_complex()
                and cat.left == cat.right.left
                and cat.direction == FORWARD and cat.right.direction == FORWARD)
                
    @staticmethod
    def is_relativiser(cat):
    	'''Recognise categories of the shape {N,NP,QP,S}`|S[dcl]$. Roughly,
any modifier category seeking a verbal category is a relativiser category.'''
        return (cat.is_complex() 
            and (is_rooted_in(N, cat.left) 
              or is_rooted_in(NP, cat.left) 
              or is_rooted_in(QP, cat.left) 
              or is_rooted_in(S, cat.left, respecting_features=True)) # for (S/S)/(S[dcl]|NP) and ((S/S)/(S/S))/(S[dcl]|NP)
            and is_rooted_in(Sdcl, cat.right, respecting_features=True))
            
    is_verbal_category = staticmethod(lambda cat: is_rooted_in(Sdcl, cat, respecting_features=True))

    def fix_categories_starting_from(self, node, until):
        '''Adjusts category labels from _node_ to _until_ (not inclusive) to obtain the correct
CCG analysis.'''
        while node is not until:
            # Only fix binary rules
            if (not node.parent) or node.parent.count() < 2: break

            l, r, p = node.parent[0], node.parent[1], node.parent
            L, R, P = (n.category for n in (l, r, p))
            debug("L: %s R: %s P: %s", L, R, P)

            applied_rule = analyse(L, R, P)
            debug("[ %s'%s' %s'%s' -> %s'%s' ] %s",
                L, ''.join(l.text()), R, ''.join(r.text()), P, ''.join(p.text()),
                applied_rule)

            if applied_rule is None:
                debug("invalid rule %s %s -> %s", L, R, P)
                
                if R.is_complex() and R.left.is_complex() and L == R.left.right:
                    # L       (X|L)|Y -> X|Y becomes
                    # X|(X|L) (X|L)|Y -> X|Y
                    T = R.left.left
                    new_category = typeraise(L, T, TR_FORWARD)#T/(T|L)
                    node.parent[0] = Node(l.tag, [l], new_category, head_index=0)

                    new_parent_category = fcomp(new_category, R)
                    if new_parent_category:
                        debug("new parent category: %s", new_parent_category)
                        p.category = new_parent_category

                    debug("New category: %s", new_category)
                
                elif L.is_complex() and L.left.is_complex() and R == L.left.right:
                    # (X|R)|Y R       -> X|Y  becomes
                    # (X|R)|Y X|(X|R) -> X|Y
                    T = L.left.left
                    new_category = typeraise(R, T, TR_BACKWARD)#T|(T/R)
                    node.parent[1] = Node(r.tag, [r], new_category, head_index=0)

                    new_parent_category = bxcomp(L, new_category)
                    if new_parent_category:
                        debug("new parent category: %s", new_parent_category)
                        p.category = new_parent_category

                    debug("New category: %s", new_category)

                # conj R -> P
                # Make P into R[conj]
                # L cannot be the comma category (,), otherwise we get a mis-analysis
                # in 2:22(5)
                if str(L) in ('conj', 'LCM'):
                    p.category = R.clone_adding_feature('conj')
                    debug("New category: %s", p.category)

                # L R[conj] -> P
                elif R.has_feature('conj'):
                    new_L = L.clone()

                    r.category = new_L.clone_adding_feature('conj')
                    p.category = new_L

                    debug("New category: %s", new_L)

                elif L.is_leaf():
                    # , R -> P[conj] becomes , R -> R[conj]
                    if P.has_feature('conj') and l.tag in ('PU', 'CC'): # treat as partial coordination
                        debug("Fixing coordination: %s" % P)
                        p.category = r.category.clone_adding_feature('conj')
                        debug("new parent category: %s" % p.category)
                        
                    # , R -> P becomes , R -> R
                    elif l.tag == "PU" and not P.has_feature('conj'): # treat as absorption
                        debug("Fixing left absorption: %s" % P)
                        p.category = r.category

                    # L       (X|L)|Y -> X|Y becomes
                    # X|(X|L) (X|L)|Y -> X|Y
                    elif R.is_complex() and R.left.is_complex() and L == R.left.right:
                        T = R.left.left
                        new_category = typeraise(L, T, TR_FORWARD)#T/(T|L)
                        node.parent[0] = Node(l.tag, [l], new_category, head_index=0)

                        new_parent_category = fcomp(new_category, R)
                        if new_parent_category:
                            debug("new parent category: %s", new_parent_category)
                            p.category = new_parent_category

                        debug("New category: %s", new_category)
                        
                elif R.is_leaf():
                    # R , -> P becomes R , -> R
                    if r.tag == "PU": # treat as absorption
                        debug("Fixing right absorption: %s" % P)
                        p.category = l.category

                    # (X|R)|Y R       -> X|Y  becomes
                    # (X|R)|Y X|(X|R) -> X|Y
                    elif L.is_complex() and L.left.is_complex() and R == L.left.right:
                        T = L.left.left
                        new_category = typeraise(R, T, TR_BACKWARD)#T|(T/R)
                        node.parent[1] = Node(r.tag, [r], new_category, head_index=0)

                        new_parent_category = bxcomp(L, new_category)
                        if new_parent_category:
                            debug("new parent category: %s", new_parent_category)
                            p.category = new_parent_category

                        debug("New category: %s", new_category)

                else:
                    new_parent_category = None
                    
                    # try typeraising fix
                    # T/(T/X) (T\A)/X -> T can be fixed:
                    # (T\A)/((T\A)/X) (T\A)/X -> T\A
                    if self.is_topicalisation(L) and (
                        L.right.right == R.right and
                        P == L.left and P == R.left.left):
                        T_A = R.left
                        X = R.right

                        l.category = T_A/(T_A/X)
                        new_parent_category = T_A
                        
                    # (X|X)|Z Y       -> X becomes
                    # (X|X)|Z X|(X|X) -> X|Z
                    elif L.is_complex() and L.left.is_complex() and R == L.left.right:
                        T = L.left.left
                        new_category = typeraise(R, R, TR_BACKWARD, strip_features=False)#T/(T|L)
                        node.parent[1] = Node(r.tag, [r], new_category, head_index=0)

                        new_parent_category = bxcomp(L, new_category)
                        if new_parent_category:
                            debug("new parent category: %s", new_parent_category)
                            p.category = new_parent_category

                        debug("New category: %s", new_category)
                                            
                    # Generalise over right modifiers of verbal categories (S[dcl]\X)$
                    elif self.is_verbal_category(L) and L.is_complex() and L.left.is_complex():
                        T = L.left.right
                        new_category = typeraise(R, T, TR_BACKWARD)
                        debug('Trying out %s', new_category)
                        
                        if bxcomp(L, new_category):
                            node.parent[1] = Node(r.tag, [r], new_category, head_index=0)
                            new_parent_category = bxcomp(L, new_category)

                    # Last ditch: try all of the composition rules to generalise over L R -> P
                    if not new_parent_category:
                        # having fxcomp creates bad categories in NP(IP DEC) construction (1:97(3))
                        # but, we need fxcomp to create the gap NP-TPC NP-SBJ(*T*) VP, so allow it when the rhs doesn't look like the DEC category
                        new_parent_category = (fcomp(L, R) or bcomp(L, R, when=not self.is_relativiser(R)) 
                                            or bxcomp(L, R, when=not self.is_relativiser(R)) #or bxcomp2(L, R, when=self.is_verbal_category(L)) 
                                            or fxcomp(L, R, when=not self.is_relativiser(R)))

                    if new_parent_category:
                        debug("new parent category: %s", new_parent_category)
                        p.category = new_parent_category
                    else:
                        debug("couldn't fix, skipping")

            node = node.parent
            debug('')

    #@echo
    def fix_subject_extraction(self, _, n, pred, w=None, reduced=False):
        global use_bare_N
        
        debug("%s", reduced)
        node = n
        debug("Fixing subject extraction: %s", lrp_repr(node))

        # We only want this if we are using the N -> NP unary rule
        # This 'fix' lets us rewrite NP(WHNP CP) as NP(CP) with categories NP(N)
        if use_bare_N and pred.tag.startswith('NP'):
            # Fix for the NP(VP de) case:
            # ---------------------------
            #         NP                 NP
            #        /  \                |  
            #      WHNP  CP     -->      CP              
            #            / \            /  \           
            #          IP  DEC         IP   DEC
            if not pred.is_leaf():
                pred.kids.pop(0)
                pred.head_index = 0
        else:
            if not reduced:
                self.remove_null_element(node)

        if w:
            index = get_trace_index_from_tag(w.tag)
        else:
            index = ''
            
        expr = r'*=PP < { *=P < { /NP-SBJ/=T << ^/\*T\*%s/ $ *=S } }' % index

        for trace_NP, ctx in find_all(node, expr, with_context=True):
            pp, p, t, s = ctx.pp, ctx.p, ctx.t, ctx.s

            self.fix_object_gap(pp, p, t, s)
            self.fix_categories_starting_from(s, until=node)

            if not self.relabel_relativiser(pred):
                # TOP is the shrunk VP
                # after shrinking, we can get VV or VA here
                # left_to_right so that we find the right node (used to match against the CP 已建成的 in 4:45(7))
                result = get_first(node, r'{ /([ICV]P|V[VA]|VRD|VSB|VCD)/=TOP $ *=SS } ! > /([ICV]P|V[VA]|VRD|VSB|VCD)/', with_context=True, left_to_right=True)
                if not result:
                    debug('Could not find verbal category; did not create null relativiser.')
                    return
                
                top, context = result
                SS = context.ss.category
                
                debug("Creating null relativiser unary category: %s", SS/SS)
                replace_kid(top.parent, top, Node("NN", [top], SS/SS, head_index=0))

    #@echo
    def fix_nongap_extraction(self, _, n, pred, k):
        node = n
        debug("Fixing nongap extraction: %s", pprint(node))
        debug("k %s", pprint(k))
        self.remove_null_element(node)

        index = get_trace_index_from_tag(k.tag)
        expr = (r'*=PP < { *=P < { /[NPQ]P(?:-%(tags)s)?%(index)s/=T << ^/\*T\*/ $ *=S } }' 
             % { 'tags': ModifierTagsRegex, 'index': index })

        # we use "<<" in the expression, because fix_*_topicalisation comes
        # before fix_nongap_extraction, and this can introduce an extra layer between
        # the phrasal tag and the trace
        for trace_NP, ctx in find_all(node, expr, with_context=True):
            pp, p, t, s = ctx.pp, ctx.p, ctx.t, ctx.s

            # remove T from P
            # replace P with S
            self.fix_object_gap(pp, p, t, s)

            if not self.relabel_relativiser(pred):
                top, context = get_first(node, r'/[ICV]P/=TOP $ *=SS', with_context=True)
                ss = context.ss

                debug("Creating null relativiser unary category: %s", ss.category/ss.category)
                replace_kid(top.parent, top, Node("NN", [top], ss.category/ss.category, head_index=0))

    def fix_ip_app(self, p, a, s):
        debug("Fixing IP-APP NX: %s", lrp_repr(p))
        new_kid = copy(a)
        new_kid.tag = base_tag(new_kid.tag) # relabel to stop infinite matching
        replace_kid(p, a, Node("NN", [new_kid], s.category/s.category, head_index=0))

    def fix_object_extraction(self, _, n, pred, w=None, reduced=False):
        global use_bare_N
        
        node = n
        debug("Fixing object extraction: %s", lrp_repr(node))
        
        # We only want this if we are using the N -> NP unary rule
        # This 'fix' lets us rewrite NP(WHNP CP) as NP(CP) with categories NP(N)
        if use_bare_N and pred.tag.startswith('NP'):
            # Fix for the NP(VP de) case:
            # ---------------------------
            #         NP                 NP
            #        /  \                |  
            #      WHNP  CP     -->      CP              
            #            / \            /  \           
            #          IP  DEC         IP   DEC          
            if not pred.is_leaf():
                pred.kids.pop(0)
                pred.head_index = 0
        else:
            if not reduced:
                self.remove_null_element(node)
        
        if w:
            index = get_trace_index_from_tag(w.tag)
        else:
            index = ''
            
        expr = r'/IP/=TOP << { *=PP < { *=P < { /NP-(OBJ|EXT)/=T << ^/\*T\*%s/ $ *=S } } }' % index

        for trace_NP, ctx in find_all(node, expr, with_context=True):
            top, pp, p, t, s = ctx.top, ctx.pp, ctx.p, ctx.t, ctx.s

            self.fix_object_gap(pp, p, t, s)
            self.fix_categories_starting_from(s, until=top)

            # If we couldn't find the DEC node, this is the null relativiser case
            if not self.relabel_relativiser(pred):
                # TOP is the S node
                # null relativiser category comes from sibling of TOP
                # if TOP has no sibling, then we're likely inside a NP-PRD < CP reduced relative (cf 1:2(9))
                result = get_first(top, r'* $ *=SS', with_context=True, nonrecursive=True)
                if result:
                    _, ctx = result; ss = ctx.ss
                    debug("Creating null relativiser unary category: %s", ss.category/ss.category)
                    replace_kid(top.parent, top, Node("NN", [top], ss.category/ss.category, head_index=0))

    def relabel_bei_category(self, top, pred):
        # particle 'you' is tagged as a preposition but acts as the BEI marker
        bei, ctx = get_first(top, r'*=S [ $ /LB/=BEI | $ ^"由"=BEI | $ ^"经"=BEI | $ ^"经过"=BEI | $ ^"随"=BEI | $ ^"为"=BEI | $ ^"以"=BEI | $ ^"经由"=BEI ]', with_context=True)
        s, bei = ctx.s, ctx.bei

        bei.category = bei.category.clone_with(right=s.category)
        bei.category.left._right = pred.category
        
        bei.parent.category = bei.category.left
        
        debug("new bei category: %s", bei.category)
        return bei
        
    def relabel_ba_category(self, top, ba):
        _, ctx = get_first(top, r'*=S $ /BA/=BA', with_context=True)
        s, ba = ctx.s, ctx.ba

        ba.category = ba.category.clone_with(right=s.category)
        
        debug("new ba category: %s", ba.category)
        return ba

    def fix_reduced_long_bei_gap(self, node, *args, **kwargs):
        debug("Fixing reduced long bei gap: %s", lrp_repr(node))

        return self.fix_long_bei_gap(node, *args, **update(kwargs, reduced=True))
        
    def fix_reduced(self, f):
        def _f(node, *args, **kwargs):
            return f(node, *args, **update(kwargs, reduced=True))
        return _f

    def fix_long_bei_gap(self, node, bei, pred, top, n=None, reduced=False):
        debug("Fixing long bei gap: %s", lrp_repr(node))

        if not reduced:
            self.remove_null_element(top)
            
        if n:
            index = get_trace_index_from_tag(n.tag)
        else:
            index = r'\*'

        expr = r'*=PP < { *=P < { /NP-(?:TPC|OBJ)/=T < ^/%s/a $ *=S } }' % index
        trace_NP, ctx = get_first(top, expr, with_context=True)

        pp, p, t, s = ctx.pp, ctx.p, ctx.t, ctx.s
        # remove T from P
        # replace P with S
        self.fix_object_gap(pp, p, t, s)

        self.fix_categories_starting_from(s, until=top)
        self.relabel_bei_category(top, pred)
        
        top.category = top[0].category.left

        debug("done %s", pprint(top))

    def fix_ba_object_gap(self, node, top, c, ba):
        debug("Fixing ba-construction object gap: %s" % lrp_repr(node))

        for trace_NP, ctx in find_all(top, r'*=PP < {*=P < { /NP-OBJ/=T < ^/\*-/ $ *=S } }', with_context=True):
            debug("Found %s", trace_NP)
            pp, p, t, s = ctx.pp, ctx.p, ctx.t, ctx.s

            self.fix_object_gap(pp, p, t, s)
            self.fix_categories_starting_from(s, until=c)
            
        self.relabel_ba_category(top, ba)

    @staticmethod
    def fix_object_gap(pp, p, t, s):
        '''Given a trace _t_, its sibling _s_, its parent _p_ and its grandparent _pp_, replaces _p_ with its sibling.'''
        p.kids.remove(t)
        replace_kid(pp, p, s)
        
    def fix_whword_topicalisation(self, node, p, s, t):
        debug('Fixing wh-word topicalisation: node: %s', lrp_repr(node))
        # stop this method from matching again (in case there's absorption on the top node, cf 2:22(5))
        t.tag = base_tag(t.tag, strip_cptb_tag=False)
        # create topicalised category based on the tag of T
        typeraise_t_category = ptb_to_cat(t)
        # insert a node with the topicalised category
        replace_kid(p, t, Node(
            base_tag(t.tag, strip_cptb_tag=False),
            [t],
            typeraise(typeraise_t_category, SbNP, TR_TOPICALISATION),
            head_index=0))
            
        index = get_trace_index_from_tag(t.tag)
        
        expr = r'*=PP < { /VP/=P < { /NP-(?:SBJ|OBJ)/=T < ^/\*T\*%s/ $ *=S } }' % index
        
        for top, ctx in find_all(p, expr, with_context=True):
            replace_kid(ctx.pp, ctx.p, ctx.s)
            self.fix_categories_starting_from(ctx.s, until=top)

    def fix_topicalisation_with_gap(self, node, p, s, t):
        debug("Fixing topicalisation with gap:\nnode=%s\ns=%s\nt=%s", lrp_repr(node), pprint(s), pprint(t))

        # stop this method from matching again (in case there's absorption on the top node, cf 2:22(5))
        t.tag = base_tag(t.tag, strip_cptb_tag=False)
        # create topicalised category based on the tag of T
        typeraise_t_category = ptb_to_cat(t)
        # insert a node with the topicalised category
        replace_kid(p, t, Node(
            base_tag(t.tag, strip_cptb_tag=False),
            [t],
            typeraise(typeraise_t_category, S, TR_TOPICALISATION),
            head_index=0))

        index = get_trace_index_from_tag(t.tag)

        # attested gaps:
        # 575 IP-TPC:t
        # 134 NP-TPC:t
        #  10 IP-Q-TPC:t
        #   8 CP-TPC:t
        #   4 NP-PN-TPC:t
        #   2 QP-TPC:t
        #   2 NP-TTL-TPC:t
        #   1 PP-TPC:t
        #   1 IP-IJ-TPC:t
        #   1 INTJ-TPC:t
        #   1 CP-Q-TPC:t
        #   1 CP-CND-TPC:t
        expr = r'/IP/=TOP << { *=PP < { *=P < { /[NICQP]P-(?:SBJ|OBJ)/=T < ^/\*T\*%s/ $ *=S } } }' % index

        for top, ctx in find_all(s, expr, with_context=True):
            debug('top: %s', pprint(top))
            self.fix_object_gap(ctx.pp, ctx.p, ctx.t, ctx.s)
            self.fix_categories_starting_from(ctx.s, until=top)

    def fix_topicalisation_without_gap(self, node, p, s, t):
        debug("Fixing topicalisation without gap: %s", pprint(node))

        new_kid = copy(t)
        new_kid.tag = base_tag(new_kid.tag, strip_cptb_tag=False)

        new_category = featureless(p.category)/featureless(s.category)
        replace_kid(p, t, Node(t.tag, [new_kid], new_category, head_index=0))

    def fix_prodrop(self, node, pp, p):
        #      X=PP
        #      |
        #      NP=P
        #      |
        #    -NONE- '*pro*'
        pp.head_index = 0
        pp.kids.remove(p)

        # this step happens after fix_rc, and object extraction with subject pro-drop can
        # lead to a pro-dropped node like:
        #        X
        #        |
        #     S/(S\NP)=PP
        #        |
        #       NP=P
        #        |
        #   -NONE- '*pro*'
        # In this case, we want to remove the whole structure
        if (not pp.kids) and pp.parent:
            ppp = pp.parent
            ppp.head_index = 0
            ppp.kids.remove(pp)

    def fix_modification(self, node, p, s, t):
        debug("Fixing modification: %s", lrp_repr(node))
        S, P = s.category, p.category

        # If you don't strip the tag :m from the newly created child (new_kid),
        # the fix_modification pattern will match infinitely when tgrep visits new_kid
        new_kid = copy(t)
        new_kid.tag = base_tag(new_kid.tag, strip_cptb_tag=False)

        new_category = featureless(P) / featureless(S)
        debug("Creating category %s", new_category)
        replace_kid(p, t, Node(t.tag, [new_kid], new_category, head_index=0))

