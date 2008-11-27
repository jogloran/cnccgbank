from __future__ import with_statement

from munge.trees.traverse import nodes
from munge.penn.io import parse_tree
from munge.penn.nodes import Node, Leaf
from munge.trees.pprint import pprint

from munge.proc.filter import Filter
import sys, re, os

from apps.identify_lrhca import *

def label_adjunction(node):
    kids = map(label_node, node.kids)
    last_kid, second_last_kid = kids.pop(), kids.pop()

    cur = Node(node.tag, [second_last_kid, last_kid])

    while kids:
        kid = kids.pop()
        cur = Node(node.tag, [kid, cur])
 
    return cur
    
def label_coordination(node):
    def label_nonconjunctions(kid):
        if kid.tag not in ('CC', 'PU'): 
            return label_node(kid)
        else: return kid
    
    kids = map(label_nonconjunctions, node.kids)
    return label_adjunction(Node(node.tag, kids))

def label_head_initial(node):
    kids = map(label_node, node.kids)[::-1]
    first_kid, second_kid = kids.pop(), kids.pop()

    cur = Node(node.tag, [first_kid, second_kid])

    while kids:
        kid = kids.pop()
        cur = Node(node.tag, [cur, kid])
    
    return cur

def label_head_final(node):
    return label_adjunction(node)

def label_predication(node):
#    return Node(node.tag, map(label_node, node.kids))
    return label_adjunction(node)
    
def label_root(node):
    final_punctuation_stk = []
    while (not node.is_leaf()) and node.kids[-1].tag.startswith('PU'):
        final_punctuation_stk.append( node.kids.pop() )
        
    result = label_node(node)
    tag = result.tag
    
    while final_punctuation_stk:
        result = Node(tag, [result, final_punctuation_stk.pop()])
        
    return result
    
def label_node(node):
    if node.is_leaf(): return node
    elif node.count() == 1: 
        node.kids[0] = label_node(node.kids[0])
        return node
    elif is_predication(node):
        return label_predication(node)
    elif is_np_internal_structure(node):
        return label_adjunction(node)
    elif is_apposition(node):
        return label_adjunction(node)
    elif is_modification(node):
        return label_adjunction(node)
    elif is_adjunction(node):
        return label_adjunction(node)
    elif is_head_final(node):
        return label_head_final(node)
    elif is_head_initial(node):
        return label_head_initial(node)
    elif is_coordination(node):
        return label_coordination(node)
    else:
        return label_adjunction(node)
        
class Binariser(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        bundle.derivation = label_root(bundle.derivation)
        self.write_derivation(bundle)
        
    def write_derivation(self, bundle):
        if not os.path.exists(self.outdir): os.makedirs(self.outdir)
        output_filename = os.path.join(self.outdir, "chtb_%02d%02d.fid" % (bundle.sec_no, bundle.doc_no))

        with file(output_filename, 'a') as f:
            print >>f, bundle.derivation
    
if __name__ == '__main__':
    docs = parse_tree(sys.stdin.read())

    for root in docs:
        # if is_predication(root):
        #     result = Node(root.tag, [
        #         label_subject(root[0]),
        #         label_predicate(root[1])
        #     ])
        # else:
        result = label_root(root)
            
        print pprint(result)