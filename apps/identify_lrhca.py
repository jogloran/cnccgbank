import re

def is_np_sbj(node):
    return re.match(r'NP(-\w+)*-SBJ', node.tag) is not None

def is_vp(node):
    return node.tag == 'VP'

def is_predication(node):
    return (node.tag.startswith('IP') and 
            is_np_sbj(node[0]) and 
            is_vp(node[1]))

def is_head_final(node):
    return node[-1].tag.endswith(':h')

def is_head_initial(node):
    return node[0].tag.endswith(':h')

def is_adjunction(node):
    return node[0].tag.endswith(':a')

def is_coordination(node):
    return node[0].tag.endswith(':c')

def is_np_internal_structure(node):
    return node.tag.startswith('NP') and node.count() > 1 and all(kid.tag == 'NN' for kid in node)

FunctionTags = 'ADV TPC TMP LOC DIR BNF CND DIR IJ LGS MNR PRP'.split()
def is_modification(node):
    if node.tag == node[-1].tag:
        m = re.match(r'\w+-(\w+)', node[0].tag)
        if m and len(m.groups()) == 1:
            function_tag = m.group(1)
            if function_tag in TagStructures.FunctionTags: return True
    
    return False