# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.trees.traverse import leaves

VerbalCategories = {'VV', 'VA', 'VC', 'VE'}
    
def has_verbal_tag(node):
    try:
        return node.tag[0] == 'V' and node.tag[1] in 'VACE'
    except: return False
    
NominalCategories = {'NN', 'NR', 'NT'}

def has_noun_tag(node):
    try:
        return node.tag[0] == 'N' and node.tag[1] in 'NTR'
    except: return False

def is_verb_compound(node):
    return any(node.tag.startswith(cand) for cand in ('VPT', 'VSB', 'VRD', 'VCD', 'VNV'))
    
def has_question_tag(node):
    return node.tag == 'CP-Q'