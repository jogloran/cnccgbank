# Defines 'short forms' and constants for a number of commonly used categories.

from munge.cats.nodes import AtomicCategory
from munge.cats.parse import parse_category

S, N, NP, PP = (AtomicCategory(atom) for atom in "S N NP PP".split())
LeftAbsorbedPunctuationCats = ", . `` : ; LRB RRB".split()
RightAbsorbedPunctuationCats = ", . '' : ; LRB RRB".split()
ConjPunctuationCats = ", ; :".split()
SbNP, SfNP, NPbNP, NbN, SbNPbSbNP, \
SbS, SfS, SbNPfSbNP, conj = [parse_category(cat) for cat in
                        '''S\\NP S/NP NP\\NP N\\N (S\\NP)\\(S\\NP)
                           S\\S  S/S (S\\NP)/(S\\NP) conj'''.split()]
                                            
# Defines a short name for converting a category string to a category representation.         
C = parse_category