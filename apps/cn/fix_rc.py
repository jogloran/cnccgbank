from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first
from munge.penn.aug_nodes import Node
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.trees.pprint import pprint, aug_node_repr
from munge.util.tgrep_utils import get_first
from munge.cats.cat_defs import *
from munge.proc.tgrep.tgrep import find_all
from munge.cats.trace import analyse
from munge.cats.nodes import FORWARD, BACKWARD

class FixExtraction(Fix):
    def pattern(self): 
        return {
            r'* < { /CP/ < {/WHNP-\d/ $ {/CP/ << {/NP-SBJ/ < "-NONE-"}}}}': self.fix_subject_extraction,
            r'* < { /CP/ < {/WHNP-\d/ $ {/CP/ << {/NP-OBJ/ < "-NONE-"}}}}': self.fix_object_extraction,
            r'* < { /IP/=P < {/NP-TPC-\d/=T $ /IP/=S }}': self.fix_topicalisation_with_gap,
            r'* < { /IP/=P < {/NP-TPC:.+/=T $ /IP/=S }}': self.fix_topicalisation_without_gap
        }
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def remove_null_element(self, node):
        # Remove the null element WHNP and its trace -NONE- '*OP*' and shrink tree
        # XXX: check that we're removing the right nodes
        node[0] = node[0][1]
        
    def relabel_relativiser(self, node):
        # Relabel the relativiser category (NP/NP)\S to (NP/NP)\(S|NP)
        
        # we want the closest DEC, so we can't use the DFS implicit in tgrep
        # relativiser, context = get_first(node, r'/DEC/ $ *=S', with_context=True)
        # s = context['S']
        # 
        # print "rel", relativiser
        # print "s", s
        
        relativiser, s = node[0][1], node[0][0]
        
        relativiser.category.right = s.category
        print "New rel category: %s" % relativiser.category
        
    def typeraise(self, node):
        if not node: return
        
        typeraised_node = Node(S/(S|NP), node.tag, [ node[0] ], node)
        node[0] = typeraised_node
        
    def fcomp_children(self, node):
        print pprint(node, node_repr=aug_node_repr)
        print node[0].category, ",", node[1].category
        if not (node[0].category.is_complex() and node[1].category.is_complex()): return node.category
        
        return node[0].category.left / node[1].category.right
        
    @staticmethod
    def fcomp(l, r):
        if (l.is_leaf() or r.is_leaf() or 
            l.right != r.left or 
            l.direction != FORWARD or l.direction != r.direction): return None
            
        return l.left / r.right
        
    @staticmethod
    def bxcomp(l, r):
        if (l.is_leaf() or r.is_leaf() or
            l.left != r.right or
            l.direction != FORWARD or l.direction == r.direction): return None
            
        return r.left / l.right
            
    def fix_categories_starting_from(self, node, until):
        print "fix from %s" % node
        while node is not until:
            l, r, p = node.parent[0], node.parent[1], node.parent
            print "np0:%s\nnp1:%s\nn:%s"% (node.parent[0], node.parent[1], node.parent)
            
            L, R, P = (n.category for n in (l, r, p))
            print "L:%s\nR:%s\nP:%s"% (L, R, P)

            applied_rule = analyse(L, R, P)
            print "[ %s'%s' %s'%s' -> %s'%s' ] %s" % (L, ''.join(l.text()), R, ''.join(r.text()), P, ''.join(p.text()), applied_rule)

            if applied_rule is None:
                print "invalid rule %s %s -> %s" % (L, R, P)
                if L.is_leaf():
                    if L == R.left.right:
                        T = R.left.left
                        new_category = T/(T|L)
                        node.parent[0] = Node(new_category, node.tag, [l])

                        new_parent_category = self.fcomp(new_category, R)
                        if new_parent_category: 
                            print "new parent category: %s" % new_parent_category
                            p.category = new_parent_category
                        
                    print "New category: %s" % new_category
                    
                elif R.is_leaf():
                    if R == L.left.right:
                        T = L.left.left
                        new_category = T|(T/R)
                        node.parent[1] = Node(new_category, node.tag, [r])
                        
                        new_parent_category = self.bxcomp(L, new_category)
                        if new_parent_category: 
                            print "new parent category: %s" % new_parent_category
                            p.category = new_parent_category
                        
                    print "New category: %s" % new_category
                    
                else:
                    new_parent_category = self.fcomp(L, R) or self.bxcomp(L, R)
                    if new_parent_category:
                        print "new parent category: %s" % new_parent_category
                        p.category = new_parent_category
                        
            elif (applied_rule == 'bwd_appl' and # implies R is complex
                  R.left == R.right):
                print "generalised New category: %s" % (L|L)
                r.category = L|L                  
            
            node = node.parent
            
    def fix_subject_extraction(self, node):
        print "Fixing subject extraction: %s" % node
        self.remove_null_element(node)
        
        # Find and remove the trace
        for trace_NP_parent in find_all(node, r'* < { * < { /NP-SBJ/ < "-NONE-" } }'):
            trace_NP_parent[0] = trace_NP_parent[0][1]
        
        # trace_NP, context = get_first(node, r'/IP/=TOP << { *=PP < { *=P < { /NP-SBJ/=T < "-NONE-" $ *=S } } }', with_context=True)
        # 
        # top, p, t, s = (context[n] for n in "TOP P T S".split())
        # 
        # p.kids.remove(t)
        # self.replace_kid(top, p, s)
        
        self.relabel_relativiser(node)
        
    def fix_object_extraction(self, node):
        print "Fixing object extraction: %s" % node
        self.remove_null_element(node)
        
        trace_NP, context = get_first(node, r'/IP/=TOP << { *=PP < { *=P < { /NP-OBJ/=T < "-NONE-" $ *=S } } }', with_context=True)
        
        top, pp, p, t, s = (context[n] for n in "TOP PP P T S".split())
        
        self.fix_object_gap(pp, p, t, s)
        
        self.fix_categories_starting_from(s, until=top)
        
        print "relabel_rel(%s)" % node
        print ''.join(node.text())
        self.relabel_relativiser(node)
        
    @staticmethod
    def fix_object_gap(pp, p, t, s):
        p.kids.remove(t)
        FixExtraction.replace_kid(pp, p, s)        
        
    def fix_topicalisation_with_gap(self, node, context):
        print "Fixing topicalisation with gap: %s" % node
        p, s, t = (context[n] for n in "P S T".split())
        
        # create topicalised category
        self.replace_kid(p, t, Node(S/(S/NP), t.tag, [t]))
        
        _, ctx = get_first(s, r'/IP/=TOP << { *=PP < { *=P < { /NP-OBJ/=T < "-NONE-" $ *=S } } }', with_context=True)
        print ctx
        self.fix_object_gap(*(ctx[n] for n in "PP P T S".split()))
        
        self.fix_categories_starting_from(ctx['S'], until=ctx['TOP'])
        
    def fix_topicalisation_without_gap(self, node, context):
        print "HEY!!"
        print node
        
        p, s, t = (context[n] for n in "P S T".split())
        
        self.replace_kid(p, t, Node(S/S, t.tag, [t]))
            
    @staticmethod
    def replace_kid(node, old, new):
        # make sure you go through Node#__setitem__, not by modifying Node.kids directly,
        # otherwise parent pointers won't get updated 
        node[node.kids.index(old)] = new