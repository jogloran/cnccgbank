# Defines 'short forms' and constants for a number of commonly used categories.

from munge.cats.nodes import AtomicCategory
from munge.cats.parse import parse_category

def featureless(cat):
    print '<><>'
    print cat
    ret = cat.clone()
    ret.features = []
    for subcat in ret.nested_compound_categories():
        subcat.features = []
    print ret
    return ret

S, N, NP, PP = (AtomicCategory(atom) for atom in "S N NP PP".split())
LeftAbsorbedPunctuationCats = ", . `` : ; LRB RRB".split()
RightAbsorbedPunctuationCats = ", . '' : ; LRB RRB".split()
ConjPunctuationCats = ", ; :".split()
SbNP, SfNP, NPbNP, NbN, SbNPbSbNP, \
SbS, SfS, SbNPfSbNP, conj = [parse_category(cat) for cat in
                        '''S\\NP S/NP NP\\NP N\\N (S\\NP)\\(S\\NP)
                           S\\S  S/S (S\\NP)/(S\\NP) conj'''.split()]
Sq, Sdcl = parse_category('S[q]'), parse_category('S[dcl]')
SdclbNP = parse_category(r'S[dcl]\NP')
# Defines a short name for converting a category string to a category representation.         
C = parse_category
