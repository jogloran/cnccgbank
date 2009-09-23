from munge.trees.traverse import leaves

VerbalCategories = ('VV', 'VA', 'VC', 'VE')
    
def has_verbal_tag(node):
    return any(node.tag.startswith(cand) for cand in VerbalCategories)
    
NominalCategories = ('NN', 'NR', 'NT')

def has_noun_tag(node):
    return any(node.tag.startswith(cand) for cand in NominalCategories)

def is_verb_compound(node):
    return all((has_verbal_tag(kid) or kid.tag == 'CC') for kid in leaves(node))