from munge.cats.parse import parse_category
from munge.cats.nodes import APPLY, COMP, NULL, ALL

LeftAbsorbedPunctuationCats = ", . `` : ; LRB RRB".split()
RightAbsorbedPunctuationCats = ", . '' : ; LRB RRB".split()
ConjPunctuationCats = ", ; :".split()
SbNP, SfNP, NPbNP, NbN, SbNPbSbNP, \
SbS, SfS, SbNPfSbNP, NP = [parse_category(cat) for cat in
                        '''S\\NP S/NP NP\\NP N\\N (S\\NP)\\(S\\NP)
                           S\\S  S/S (S\\NP)/(S\\NP) NP'''.split()]

def analyse(l, r, cur, examine_modes=False):
    return (try_unary_rules(l, r, cur) if not r else \
            try_application(l, r, cur, examine_modes) or \
            try_absorption(l, r, cur) or \
            try_composition_or_substitution(l, r, cur, examine_modes))

def try_unary_rules(l, r, cur):
    '''Determines if [l r -> cur] matches any unary rules.'''
    if l == SbNP:
        for cand_cat, rule in {
            SfS: "lex_typechange",
            NP:  "lex_typechange",
            SbNPfSbNP: "lex_typechange",
            SbS: "lex_typechange"
        }.iteritems(): 
            if cur == cand_cat: return rule

    if l == SfNP and cur == NPbNP:
        return "lex_typechange"

    if cur.is_compound():
        if cur.right.is_compound(): # Type raising
            if cur.right.right == l:
                if cur.direction == FORWARD and cur.right.direction == BACKWARD:
                    return "fwd_raise"
                elif cur.direction == BACKWARD and cur.right.direction == FORWARD:
                    return "bwd_raise"

        if l.is_compound(): # Other special unary rules
            if l == SbNP:
                if cur == NPbNP or cur == NbN:
                   return "appositive_typechange"
                if cur == SbNPbSbNP:
                    return "clause_mod_typechange"

        elif not l.is_compound(): # Atomic -> atomic rules
            if l.cat == 'N' and cur.cat == 'NP': return "np_typechange"

    return None # no rule matched

def allows_application(mode_index):
    return mode_index in (APPLY, COMP, ALL)

def is_application(appl, arg, result, examine_modes=False):
    return ((not examine_modes) or allows_appl(appl.mode)) and \
            appl.right == arg and appl.left == result 

def try_application(l, r, cur, examine_modes=False):
    '''Determines if [l r -> cur] matches any application rules. If _examine_modes_ is
    true, then the modes of the arguments are checked to see if they permit application.'''
    if l.is_compound() and is_application(l, r, cur, examine_modes):
        if l.direction == FORWARD: return "fwd_appl"
    elif r.is_compound() and is_application(r, l, cur, examine_modes):
        if r.direction == BACKWARD: return "bwd_appl"

    return None

def allows_composition(mode_index):
    return mode_index in (COMP, ALL)

def is_composition(l, r, result, examine_modes=False):
    return ((not examine_modes) or (allows_comp(lhs.mode) and allows_comp(rhs.mode))) and \
            l.right == r.left and l.left == result.left and r.right == result.right

def try_composition(l, r, cur, examine_modes=False):
    '''Determines if [l r -> cur] matches any composition rules. If _examine_modes_ is
    true, then the modes of the arguments are checked to see if they permit composition.'''
    if is_composition(l, r, cur, examine_modes):
        if l.direction == FORWARD: # Forward harmonic or crossed composition
            if cur.direction == FORWARD and cur.direction == r.direction:
                return "fwd_comp"
            if cur.direction == BACKWARD and cur.direction != r.direction:
                return "fwd_xcomp"

    if is_composition(r, l, cur, examine_modes):
        if r.direction == BACKWARD: # Backward harmonic or crossed composition
            if cur.direction == FORWARD and cur.direction != r.direction:
                return "bwd_xcomp"
            if cur.direction == BACKWARD and cur.direction == r.direction:
                return "bwd_comp"

    # Recognise backward recursive crossed composition with depth 1 as a special case
    # (Y / a) /Z   X \ Y ->  (X   / a)/Z
    #  |__ | _ | _ | __|      |   |    |
    #      |   |__ | ________ | _ |____|
    #      |       |__________|   |
    #      | _____________________|
    if l.left.is_compound() and cur.left.is_compound() and \
       l.left.left == r.right and l.right == cur.right and \
       r.left == cur.left.left and l.right == cur.right:
        return "bwd_r1xcomp"

    return None

def is_substitution(l, r, cur, examine_modes=False):
    return ((not examine_modes) or (allows_comp(lhs.mode) and allows_comp(rhs.mode))) and \
            l.left.left == result.left and l.left.right == r.left and \
            l.right == r.right and r.right == result.right

def try_substitution(l, r, cur, examine_modes=False):
    if l.left.is_compound():
        if is_substitution(l, r, cur, examine_modes) and \
           l.left.direction == FORWARD:
            if l.direction == FORWARD and \
               r.direction == FORWARD and \
               cur.direction == FORWARD:
                return "fwd_subst"
            elif l.direction == BACKWARD and \
                 r.direction == BACKWARD and \
                 cur.direction == BACKWARD:
                return "fwd_xsubst"
    elif r.left.is_compound():
        if is_substitution(r, l, cur, examine_modes) and \
           r.left.direction == BACKWARD:
            if r.direction == FORWARD and \
               l.direction == FORWARD and \
               cur.direction == FORWARD:
                return "bwd_xsubst"
            elif r.direction == BACKWARD and \
                 l.direction == BACKWARD and \
                 cur.direction == BACKWARD:
                return "bwd_subst"

    return None

def try_composition_or_substitution(l, r, cur, examine_modes=False):
    if l.is_compound() or r.is_compound() or cur.is_compound():
        return try_composition(l, r, cur, examine_modes) or \
               try_substitution(l, r, cur, examine_modes)

    return None

def try_absorption(l, r, cur):
    if r.has_feature("conj") and l == r and l == cur: return "conjoin"

    if not l.is_compound():
        if cur.has_feature("conj"):
            if l.cat in ConjPunctuationCats: return "conj_comma_absorb"
            if l.cat == "conj": return "conj_absorb"

        if cur == SbNPbSbNP and l.cat == "," and str(r) == "NP":
            return "appositive_comma_absorb"
        if str(cur) == "N" and l.cat == "conj" and str(r) == "N":
            return "funny_conj" # conj N -> N is the funny conj rule

        if l.cat in LeftAbsorbedPunctuationCats and r == cur:
            return "l_punct_absorb"

    if not r.is_compound() and r.cat in RightAbsorbedPunctuationCats and l == cur:
        return "r_punct_absorb"

    return None
