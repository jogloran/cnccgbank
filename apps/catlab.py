from __future__ import with_statement
from munge.proc.filter import Filter
import os

from apps.identify_lrhca import *
from munge.cats.nodes import *
from munge.cats.cat_defs import *
from munge.util.err_utils import info

def label_predication(node):
    node.category = ptb_to_cat(node.tag)
    label(node[0])
    
    node[1].category = node.category | node[0].category
    
    label(node[1])
    
def label_adjunction(node):
    print "label_adj(%s)" % node
    node[0].category = node.category / node.category
    label(node[0])
        
    node[1].category = node.category
    label(node[1])
    
def label_head_final(node):
    node[0].category = label(node[0])
    label(node[0])
    
    node[1].category = node.category | node[0].category
    label(node[1])
    
def label_head_initial(node):
    print "label_head_initial(%s)" % node
    node[1].category = label(node[1])
    label(node[1])
    
    node[0].category = node.category / node[1].category
    label(node[0])
    
def label_coordination(node):
    pass
    
def ptb_to_cat(ptb_tag):
#    print ptb_tag
    return S
    
def label(node):
    if node.is_leaf(): 
        node.category = ptb_to_cat(node.tag)
    elif node.count() == 1: 
        node.category = ptb_to_cat(node.tag)
        label(node[0])
        
    elif is_predication(node):
        label_predication(node)
    elif is_np_internal_structure(node):
        label_adjunction(node)
    elif is_adjunction(node):
        label_adjunction(node)
    elif is_head_final(node):
        label_head_final(node)
    elif is_head_initial(node):
        label_head_initial(node)
    elif is_coordination(node):
        label_coordination(node)
    else:
        node.category = C('??')
        for kid in node:
            kid.category = C('??')
            label(kid)
            
#    print node

class LabelNodes(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        label(bundle.derivation)
        
        self.write_derivation(bundle)
        
    def write_derivation(self, bundle):
        if not os.path.exists(self.outdir): os.makedirs(self.outdir)
        output_filename = os.path.join(self.outdir, "chtb_%02d%02d.fid" % (bundle.sec_no, bundle.doc_no))

        with file(output_filename, 'a') as f:
            print >>f, bundle.derivation