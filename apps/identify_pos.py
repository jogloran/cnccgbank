from munge.trees.traverse import leaves

VerbalCategories = ('VV', 'VA', 'VC', 'VE')
    
def has_verbal_tag(node):
    try:
        return node.tag[0] == 'V' and node.tag[1] in ('V', 'A', 'C', 'E')
    except: return False
    
NominalCategories = ('NN', 'NR', 'NT')

def has_noun_tag(node):
    try:
        return node.tag[0] == 'N' and node.tag[1] in ('N', 'T', 'R')
    except: return False

def is_verb_compound(node):
    return all((has_verbal_tag(kid) or kid.tag == 'CC') for kid in leaves(node))