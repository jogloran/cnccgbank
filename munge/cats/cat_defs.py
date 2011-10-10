# Defines 'short forms' and constants for a number of commonly used categories.

from munge.cats.nodes import AtomicCategory
from munge.cats.parse import parse_category
from munge.util.config import config

def featureless(cat):
    ret = cat.clone()
    ret.features = []
    for subcat in ret.nested_compound_categories():
        subcat.features = []
    return ret

S, N, NP, PP = (AtomicCategory(atom) for atom in "S N NP PP".split())

LeftAbsorbedPunctuationCats = ", . `` : ; LRB RRB".split()
RightAbsorbedPunctuationCats = ", . '' : ; LRB RRB".split()
ConjPunctuationCats = ", ; :".split()

if config.cn_puncts:
    LeftAbsorbedPunctuationCats +=  "LCM LPA RPA LQU RQU LSQ RSQ LTL RTL LCD RCD LCS RCS DSH SLS ? !".split()
    RightAbsorbedPunctuationCats += "LCM LPA RPA LQU RQU LSQ RSQ LTL RTL LCD RCD LCS RCS DSH SLS ? !".split()
    ConjPunctuationCats.append("LCM")

SbNP, SfNP, NPbNP, NPfNP, NbN, NfN, SbNPbSbNP, \
SbS, SfS, SbNPfSbNP, conj = [parse_category(cat) for cat in
                        '''S\\NP S/NP NP\\NP NP/NP N\\N N/N (S\\NP)\\(S\\NP)
                           S\\S S/S (S\\NP)/(S\\NP) conj'''.split()]
                           
# Chinese topicalised cats
SfSfNP, SfSfS = parse_category(r'S/(S/NP)'), parse_category(r'S/(S/S)')
QP = parse_category('QP')

SbNPfNP = parse_category(r'(S\NP)/NP')
SdclbNPfNP = parse_category(r'(S[dcl]\NP)/NP')
Sq, Sdcl = parse_category('S[q]'), parse_category('S[dcl]')
SadjbNP = parse_category(r'S[adj]\NP')
SdclbNP, Sfrg = parse_category(r'S[dcl]\NP'), parse_category(r'S[frg]')
Nnum = parse_category(r'N[num]')
# Defines a short name for converting a category string to a category representation.         
C = parse_category
