import re, copy

from apps.cn.catlab import ptb_to_cat

from apps.util.echo import echo

from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first, find_all
from munge.penn.aug_nodes import Node

from munge.trees.pprint import pprint, aug_node_repr
from munge.util.tgrep_utils import get_first
from munge.cats.cat_defs import *
from munge.cats.trace import analyse
from munge.cats.nodes import FORWARD, BACKWARD
from munge.trees.traverse import lrp_repr

from munge.util.err_utils import warn, debug

from apps.cn.output import OutputCCGbankDerivation
from apps.cn.fix import Fix
from apps.cn.fix_utils import *

from apps.identify_lrhca import base_tag

class FixExtraction(Fix):
    def pattern(self): 
        return list((
            (r'*=TOP < { /LB/=BEI $ { /CP/ < {/WHNP-\d+/ $ {/[CI]P/ << {/NP-(?:TPC|OBJ)/ < ^/\*T\*/}}}}}', self.fix_long_bei_gap),
            
            # TODO: needs to be tested with (!NP)-TPC
            (r'/IP/=P < {/[^-]+-TPC-\d+:t/=T $ /IP/=S }', self.fix_topicalisation_with_gap),
            (r'/IP/=P < {/[^-]+-TPC:T/=T $ /IP/=S }', self.fix_topicalisation_without_gap),
        
            # Adds a unary rule when there is a clash between the modifier type (eg PP-PRD -> PP) 
            # and what is expected (eg S/S)
            # This should come first, otherwise we get incorrect results in cases like 0:5(7).
            (r'*=P <1 {/:m$/a=T $ *=S}', self.fix_modification),
            
               # long bei-construction admits deletion of the object inside the S complement when it co-refers to the subject of bei.
            #   (r'', self.fix_long_bei_gap),
            
            # The node [CI]P will be CP for the normal relative clause construction (CP < IP DEC), and
            # IP for the null relativiser construction.
            # TODO: unary rule S[dcl]|NP -> N/N is only to apply in the null relativiser case.
            (r'* < { /CP/ < {/WHNP-\d+/ $ {/[CI]P/ << {/NP-SBJ/ < ^/\*T\*/}}}}', self.fix_subject_extraction),
            (r'* < { /CP/ < {/WHNP-\d+/ $ {/[CI]P/ << {/NP-OBJ/ < ^/\*T\*/}}}}', self.fix_object_extraction),
            (r'* < { /CP/ < {/WH[NP]P-\d+/ $ {/[CI]P/ << {/[NP]P-(?:TPC|LOC|EXT|ADV|DIR|IO|LGS|MNR|PN|PRP|TMP|TTL)/ < ^/\*T\*/}}}}', self.fix_nongap_extraction),
            
            # 
            (r'* < { /IP-APP/=A $ /N[NRT]/=S }', self.fix_ip_app),
         
            # ba-construction object gap
            (r'*=TOP < { /BA/ $ { * << ^/\*-/ }=C }', self.fix_ba_object_gap),
            
            # Removes the prodrop trace *pro*
            (r'*=PP < { *=P < ^"*pro*" }', self.fix_prodrop),
        ))
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def remove_null_element(self, node):
        # Remove the null element WHNP and its trace -NONE- '*OP*' and shrink tree
        pp, context = get_first(node, r'*=PP < { *=P < { /WH[NP]P/=T $ *=S } }', with_context=True)
        p, t, s = context['P'], context['T'], context['S']
        
        replace_kid(pp, p, s)
        
    def remove_PRO_gap(self, node):
        node[1] = node[1][1]
        
    def relabel_relativiser(self, node):
        # Relabel the relativiser category (NP/NP)\S to (NP/NP)\(S|NP)
        
        # we want the closest DEC, so we can't use the DFS implicit in tgrep
        # relativiser, context = get_first(node, r'/DEC/ $ *=S', with_context=True)
        # s = context['S']
        result = get_first(node, r'*=S $ /DEC/=REL', with_context=True)
        if result is not None:
            _, context = result
            s, relativiser = context['S'], context['REL']
            
            relativiser.category.right = s.category
            debug("New rel category: %s", relativiser.category)
            
            return True
        else:
            warn("Couldn't find relativiser under %s", node)
            return False
        
    @classmethod
    def fcomp(C, l, r):
        if (l.is_leaf() or r.is_leaf() or 
            l.right != r.left or 
            l.direction != FORWARD or l.direction != r.direction): return None
            
        return C.fake_unify(l, r, l.left / r.right)
                
    @classmethod
    def bxcomp(C, l, r):
        # Y/Z X\Y -> X/Z
        if (l.is_leaf() or r.is_leaf() or
            l.left != r.right or
            l.direction != FORWARD or l.direction == r.direction): return None
            
        return C.fake_unify(l, r, r.left / l.right)
        
    @classmethod
    def fxcomp(C, l, r):
        if (l.is_leaf() or r.is_leaf() or
            l.right != r.left or
            l.direction != FORWARD or r.direction == l.direction): return None

        return C.fake_unify(l, r, l.left | r.right)
        
    @staticmethod
    def fake_unify(l, r, result):
        # Fake unification onto result category
        # 1. get inner-most result category from R
        # 2. give its features to L's result category
        # 3. ???
        # 4. Profit!!!
        
        result = result.clone()
        
        cur = r
        while cur.is_complex(): cur = cur.left
        
        res = result
        while res.is_complex(): res = res.left
        res.features = copy.copy(cur.features)
        
        return result

        
    FORWARD, BACKWARD, TOPICALISATION = 1, 2, 3
    @classmethod
    def typeraise(C, x, t, dir):
        '''
        Performs the typeraising X -> T|(T|X).
        '''
        T, X = featureless(t), featureless(x)
        
        if dir == C.FORWARD:
            return T/(T|X)
        elif dir == C.BACKWARD:
            return T|(T/X)
        elif dir == C.TOPICALISATION:
            return T/(T/X)
        else:
            raise RuntimeException, "Invalid typeraise direction."
            
    #@echo
    def fix_categories_starting_from(self, node, until):
        debug("fix from %s to %s", node, until)
        while node is not until:
            if (not node.parent) or node.parent.count() < 2: break
            
            l, r, p = node.parent[0], node.parent[1], node.parent
            L, R, P = (n.category for n in (l, r, p))
            debug("L: %s R: %s P: %s", L, R, P)

            applied_rule = analyse(L, R, P)
            debug("[ %s'%s' %s'%s' -> %s'%s' ] %s", 
                L, ''.join(l.text()), 
                R, ''.join(r.text()), 
                P, ''.join(p.text()), 
                applied_rule)

            if applied_rule is None:
                debug("invalid rule %s %s -> %s", L, R, P)
                
                # conj R -> P
                # Make P into R[conj] 
                if str(L) in ('conj', 'LCM'):
                    p.category = R.clone().add_feature('conj')
                    debug("New category: %s", p.category)
                    
                # L R[conj] -> P
                # 
                elif R.has_feature('conj'):
                    new_L = L.clone()
                    new_L.features = []
                    
                    r.category = new_L.add_feature('conj')
                    p.category = new_L
                    
                    debug("New category: %s", new_L)
                
                elif L.is_leaf():
                    if l.tag == "PU": # treat as absorption
                        debug("Fixing left absorption: %s" % P)
                        p.category = r.category 
                        
                    elif R.is_complex() and R.left.is_complex() and L == R.left.right:
                        T = R.left.left
                        new_category = self.typeraise(L, T, self.FORWARD)#T/(T|L)
                        node.parent[0] = Node(new_category, node.tag, [l])

                        new_parent_category = self.fcomp(new_category, R)
                        if new_parent_category: 
                            debug("new parent category: %s", new_parent_category)
                            p.category = new_parent_category
                        
                        debug("New category: %s", new_category)
                    
                elif R.is_leaf():
                    if r.tag == "PU": # treat as absorption
                        debug("Fixing right absorption: %s" % P)
                        p.category = l.category
                        
                    elif L.is_complex() and L.left.is_complex() and R == L.left.right:
                        T = L.left.left
                        new_category = self.typeraise(R, T, self.BACKWARD)#T|(T/R)
                        node.parent[1] = Node(new_category, node.tag, [r])
                        
                        new_parent_category = self.bxcomp(L, new_category)
                        if new_parent_category: 
                            debug("new parent category: %s", new_parent_category)
                            p.category = new_parent_category
                        
                        debug("New category: %s", new_category)
                    
                else:
                    new_parent_category = self.fcomp(L, R) or self.bxcomp(L, R) or self.fxcomp(L, R)
                    if new_parent_category:
                        debug("new parent category: %s", new_parent_category)
                        p.category = new_parent_category
            
            node = node.parent
            
    #@echo
    def fix_subject_extraction(self, node):
        debug("Fixing subject extraction: %s", lrp_repr(node))
        self.remove_null_element(node)
        
        # Find and remove the trace
        # we use find_all to find all traces in the case of coordination
        # for trace_NP_parent in find_all(node, r'* < { * < { /NP-SBJ/ < ^/\*T\*/ } }'):
        #     trace_NP_parent[0] = trace_NP_parent[0][1]
            
        trace_NP, context = get_first(node, r'*=PP < { *=P < { /NP-SBJ/=T < ^/\*T\*/ $ *=S } }', with_context=True)
        pp, p, t, s = (context[n] for n in "PP P T S".split())
            
        self.fix_object_gap(pp, p, t, s)
        self.fix_categories_starting_from(s, until=node)
        
        if not self.relabel_relativiser(node):
            # TOP is the shrunk VP
            # after shrinking, we can get VV or VA here
            top, context = get_first(node, r'/([ICV]P|V[VA])/=TOP $ *=SS', with_context=True)
            ss = context["SS"]
            
            debug("Creating null relativiser unary category: %s", ss.category/ss.category)
            replace_kid(top.parent, top, Node(ss.category/ss.category, "NN", [top]))
        
    def fix_nongap_extraction(self, node):
        debug("Fixing nongap extraction: %s", lrp_repr(node))
        self.remove_null_element(node)
        
        # we use "<<" in the expression, because fix_*_topicalisation comes
        # before fix_nongap_extraction, and this can introduce an extra layer between
        # the phrasal tag and the trace
        trace_NP, context = get_first(node, 
            r'*=PP < { *=P < { /[NP]P-(?:TPC|LOC|EXT|ADV|DIR|IO|LGS|MNR|PN|PRP|TMP|TTL)/=T << ^/\*T\*/ $ *=S } }', with_context=True)
        pp, p, t, s = (context[n] for n in "PP P T S".split())
        
        # remove T from P
        # replace P with S
        self.fix_object_gap(pp, p, t, s)
        
        if not self.relabel_relativiser(node):
            top, context = get_first(node, r'/[IC]P/=TOP $ *=SS', with_context=True)
            ss = context["SS"]
            
            debug("Creating null relativiser unary category: %s", ss.category/ss.category)
            replace_kid(top.parent, top, Node(ss.category/ss.category, "NN", [top]))
            
    def fix_ip_app(self, p, a, s):
        debug("Fixing IP-APP NX: %s", lrp_repr(p))
        new_kid = copy.copy(a)
        new_kid.tag = base_tag(new_kid.tag) # relabel to stop infinite matching
        replace_kid(p, a, Node(s.category/s.category, "NN", [new_kid]))
        
    #@echo
    def fix_object_extraction(self, node, **vars):
        debug("Fixing object extraction: %s", lrp_repr(node))
        self.remove_null_element(node)
        
        # FIXME: this matches only once (because it's TOP being matched, not T)
        trace_NP, context = get_first(node, 
            r'/[IC]P/=TOP << { *=PP < { *=P < { /NP-OBJ/=T < ^/\*T\*/ $ *=S } } } $ *=SS', with_context=True)
    
        top, pp, p, t, s, ss = (context[n] for n in "TOP PP P T S SS".split())
    
        self.fix_object_gap(pp, p, t, s)
    
        self.fix_categories_starting_from(s, until=top)
        
        # If we couldn't find the DEC node, this is the null relativiser case
        if not self.relabel_relativiser(node):
            # TOP is the S node
            debug("Creating null relativiser unary category: %s", ss.category/ss.category)
            replace_kid(top.parent, top, Node(ss.category/ss.category, "NN", [top]))
            
    def relabel_bei_category(self, top):
        bei, context = get_first(top, r'/LB/=BEI $ *=S', with_context=True)
        s = context['S']
        
        bei.category.right = s.category
            
    def fix_long_bei_gap(self, node, top, bei):
        debug("Fixing long bei gap: %s", lrp_repr(node))
        self.remove_null_element(node)
        
        # FIXME: this matches only once (because it's TOP being matched, not T)
        trace_NP, context = get_first(node, 
            r'*=PP < { *=P < { /NP-(?:TPC|OBJ)/=T < ^/\*T\*/ $ *=S } }', with_context=True)
    
        pp, p, t, s = (context[n] for n in "PP P T S".split())
        # remove T from P
        # replace P with S
        self.fix_object_gap(pp, p, t, s)

        self.fix_categories_starting_from(s, until=top)
                
        self.relabel_bei_category(top)
            
    def fix_ba_object_gap(self, node, top, c):
        debug("Fixing ba-construction object gap: %s" % lrp_repr(node))
        
        for trace_NP, context in find_all(top, r'*=PP < {*=P < { /NP-OBJ/=T < ^/\*-/ $ *=S } }', with_context=True):
            debug("Found %s", trace_NP)
            pp, p, t, s = (context[n] for n in "PP P T S".split())
            
            self.fix_object_gap(pp, p, t, s)
            self.fix_categories_starting_from(s, until=c)
        
    @staticmethod
    def fix_object_gap(pp, p, t, s):
        debug("pp:%s\npp:%s\nt:%s\ns:%s", *map(pprint, (pp,p,t,s)))
        p.kids.remove(t)
        replace_kid(pp, p, s)
        
    def fix_topicalisation_with_gap(self, node, p, s, t):
        debug("Fixing topicalisation with gap:\nnode=%s\ns=%s", lrp_repr(node), pprint(s))

        # stop this method from matching again (in case there's absorption on the top node, cf 2:22(5))
        t.tag = self.strip_tag(t.tag)
        # create topicalised category based on the tag of T
        typeraise_t_category = ptb_to_cat(t)
        # insert a node with the topicalised category
        replace_kid(p, t, Node(
            self.typeraise(S, typeraise_t_category, self.TOPICALISATION), 
            self.strip_tag(t.tag), 
            [t]))
        
        top, ctx = get_first(s, r'/IP/=TOP << { *=PP < { *=P < { /[NIC]P-(?:SBJ|OBJ)/=T < ^/\*T\*/ $ *=S } } }', with_context=True)
        self.fix_object_gap(*(ctx[n] for n in "PP P T S".split()))
        
        self.fix_categories_starting_from(ctx['S'], until=top)
        
    def fix_topicalisation_without_gap(self, node, p, s, t):
        debug("Fixing topicalisation without gap: %s", lrp_repr(node))

        new_kid = copy.copy(t)
        new_kid.tag = self.strip_tag(new_kid.tag)
        
        replace_kid(p, t, Node(S/S, t.tag, [new_kid]))
        
    def fix_prodrop(self, node, pp, p):
        #      X=PP
        #      |
        #      NP=P
        #      |
        #    -NONE- '*pro*'
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
            ppp.kids.remove(pp)
            
    @staticmethod
    def strip_tag(tag):
        return re.sub(r':.+$', '', tag)
            
    def fix_modification(self, node, p, s, t):
        debug("Fixing modification: %s", lrp_repr(node))
        S, P = s.category, p.category

        # If you don't strip the tag :m from the newly created child (new_kid),
        # the fix_modification pattern will match infinitely when tgrep visits new_kid
        new_kid = copy.copy(t)
        new_kid.tag = self.strip_tag(new_kid.tag)
        
        new_category = featureless(P) / featureless(S)
        debug("Creating category %s", new_category)
        replace_kid(p, t, Node(new_category, t.tag, [new_kid]))
        