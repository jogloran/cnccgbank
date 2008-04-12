import unittest
import munge

from itertools import starmap, islice, izip, count

from munge.cats.paths import applications, applications_with_path, applications_per_slash_with_path
from munge.cats.parse import parse_category
from munge.cats.trace import analyse

from munge.util.iter_utils import each_pair
from munge.trees.traverse import leaves, leaves_reversed
from munge.ccg.io import CCGbankReader, Derivation

from munge.trees.traverse import get_leaf
    
def load_ccgbank_tree(fn, deriv_no):
    for doc, i in izip(CCGbankReader(fn), count()):
        if i == deriv_no: return doc.derivation
    return None


class TraceTests(unittest.TestCase):
    def testEquality(self):
        cat1 = parse_category("((A\\B)/(C/D))/((A/B)/C)")
        cat2 = parse_category("((A[f]\\B[g])/(C[h]/D[i])[j])/((A[k]/B[l])/C[m])[n]")
        cat3 = parse_category("((A[f]/B[g])\\(C[h]/D[i])[j])\\((A[k]/B[l])/C[m])[n]")

        self.failIf(cat1.equal_respecting_features(cat2))
        self.assert_(cat1 == cat2)
        self.assert_(cat1 != cat3)
    
    def test_nested_compounds(self):
        cat1 = parse_category('((A\\.B)/.(C/.D))/.((A/.B)/.C)')
        nesteds = cat1.nested_compound_categories()
        self.assertEqual([str(nested) for nested in nesteds],
                         ["((A\\.B)/.(C/.D))/.((A/.B)/.C)",
                          "(A\\.B)/.(C/.D)", "A\\.B", "C/.D",
                          "(A/.B)/.C", "A/.B"])
    
    def build_seq(self, iterable):
        for (l, r, was_flipped) in iterable:
            yield (parse_category(l), r and parse_category(r), was_flipped)
    
    def test_fappl(self):
        catseq = self.build_seq([ ["(S/NP)/(S/NP)", "(S/NP)", False],
                             ["(S/NP)"   , "NP", False],
                             ["S", ".", False],
                             ["S", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["fwd_appl", "fwd_appl", "r_punct_absorb"], apps)

    
    def test_bappl(self):
        catseq = self.build_seq([ ["S\\NP", "(S\\NP)\\(S\\NP)", False],
                             ["NP", "S\\NP", True],
                             ["S",    ".", False],
                             ["S", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["bwd_appl", "bwd_appl", "r_punct_absorb"], apps)

    
    def test_ftype(self):
        catseq = self.build_seq([ ["NP", None, False],
                             ["S/(S\\NP)", ".", False],
                             ["S/(S\\NP)", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["fwd_raise", "r_punct_absorb"], apps)

    
    def test_btype(self):
        catseq = self.build_seq([ ["NP", None, False],
                             ["S\\(S/NP)", ".", False],
                             ["S\\(S/NP)", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["bwd_raise", "r_punct_absorb"], apps)

    
    def test_ftype_fcomp(self):
        catseq = self.build_seq([ ["NP", None, False],
                             ["S/(S\\NP)", "(S\\NP)/NP", False],
                             ["S/NP", ".", False],
                             ["S/NP", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["fwd_raise", "fwd_comp", "r_punct_absorb"], apps)

    
    def test_btype_bappl(self):
        catseq = self.build_seq([ ["NP", None, False],
                             ["((S\\NP)/NP)", "(S\\NP)\\((S\\NP)/NP)", True],
                             ["NP", "S\\NP", True],
                             ["S", ".", False],
                             ["S", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["bwd_raise", "bwd_appl", "bwd_appl", "r_punct_absorb"], apps)

    
    def test_r_punct_absorb(self):
        catseq = self.build_seq([ ["NP", ".", False],
                             ["NP", ",", False],
                             ["NP", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["r_punct_absorb", "r_punct_absorb"], apps)

    
    def test_mixed_punct_absorb(self):
        catseq = self.build_seq([ ["NP", ".", False],
                             [",", "NP", True],
                             ["NP", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["r_punct_absorb", "l_punct_absorb"], apps)

    
    # From page 51 of Mark Steedman, 'The Syntactic Process'.
    def test_mixed_fsubst(self):
        catseq = self.build_seq([ ["(VP\\VP)/VP", "VP/NP", False],
                             ["VP/NP", "(VP\\VP)/NP", True],
                             ["S/VP", "VP/NP", True],
                             ["(N\\N)/(S/NP)", "S/NP", True],
                             ["N\\N", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["fwd_comp", "bwd_xsubst", "fwd_comp", "fwd_appl"], apps)

    
    def test_wsj0003_1(self):
        tree = load_ccgbank_tree("munge/tests/wsj_0003.auto", 0)
        leaf = get_leaf(tree, 10, "forwards")
        
        self.assertEqual("filters", leaf.lex)
        appls = list(applications(leaf))
        
        self.assertEqual(["fwd_appl", "fwd_appl", "np_typechange", "fwd_appl", "fwd_appl",
                      "fwd_appl", "fwd_appl", "appositive_typechange", "bwd_appl",
                      "bwd_appl", "bwd_appl", "r_punct_absorb" ], appls)

    
    def test_wsj0087_8(self):
        tree = load_ccgbank_tree("munge/tests/wsj_0087.auto", 7)
        leaf = get_leaf(tree, 6, "backwards")
        
        self.assertEqual("to", leaf.lex)
        appls = list(applications(leaf))
        
        self.assertEqual(["fwd_appl", "conj_absorb", "conjoin", "bwd_appl", "fwd_appl",
                      "bwd_appl", "fwd_appl", "fwd_appl", "r_punct_absorb"], appls)


    
    def test_punct_conj(self):
        catseq = self.build_seq([ [";", "NP", False],
                             [";", "NP[conj]", True],
                             ["NP[conj]", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["conj_comma_absorb", "conj_comma_absorb"], apps)

    
    def test_punct_conj_with_existing_feature(self):
        catseq = self.build_seq([ [":", "PP[b]", False],
                             ["PP[b][conj]", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["conj_comma_absorb"], apps)

    
    def test_appositive_comma_absorb(self):
        catseq = self.build_seq([ [",", "NP", False ],
                             ["(S\\NP)\\(S\\NP)", None, False ]])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["appositive_comma_absorb"], apps)

    
    def test_conjoin(self):
        catseq = self.build_seq([ ["NP[f]", "NP[conj]", False],
                             ["NP"   , "NP[conj]", False],
                             ["NP"   , None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["conjoin", "conjoin"], apps)

    
    def test_funny_conj(self):
        catseq = self.build_seq([ ["conj", "N", False],
                             ["N", None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual(["funny_conj"], apps)

    
    def assert_is_unary_conversion(self, frm, to, expect):
        catseq = self.build_seq([ [frm, None, False], [to, None, False] ])
        apps = list(applications_with_path(catseq))
        self.assertEqual([expect], apps)

    
    def test_lex_typechange(self):
        # S\NP -> NP\NP or N\N, (S\NP)\(S\NP) are also lex rules in the parser
        # but we call these appositive_typechange, clause_mod_typechange respectively
        # and not lex_typechange
        for cat in 'S/S NP (S\\NP)/(S\\NP) S\\S'.split():
            self.assert_is_unary_conversion("S\\NP", cat, "lex_typechange")
        
        self.assert_is_unary_conversion("S/NP", "NP\\NP", "lex_typechange")

    
    def test_by_slash(self):
        catseq = self.build_seq([ ["S\\NP", "(S\\NP)\\(S\\NP)", True],
                             ["NP", "S\\NP", True],
                             ["S",    ".", False],
                             ["S", None, False] ])
        
        apps = list(applications_per_slash_with_path(catseq, 3))
        self.assertEqual(["bwd_appl", # slash 0
                      "bwd_appl", # slash 1
                       None], apps)
    
    
    def test_by_slash_mixed(self):
        catseq = self.build_seq([ ["(VP\\VP)/VP", "VP/NP", False],
                             ["VP/NP", "(VP\\VP)/NP", True],
                             ["S/VP", "VP/NP", True],
                             ["(N\\N)/(S/NP)", "S/NP", True],
                             ["N\\N", None, False] ])
        apps = list(applications_per_slash_with_path(catseq, 2))
        self.assertEqual(["fwd_comp", # slash 0
                      None],#"bwd_xsubst"], # slash 1
                      apps)
    
    
    def test_by_slash2(self):
        # slash index:           1  2  3  4     0  5
        catseq = self.build_seq([ ["(C/(D/(E/(F/G))))/(A/B)", "(A/B)/C", False],
                             ["(C/(D/(E/(F/G))))/C", "C", False],
                             ["C/(D/(E/(F/G)))", "D/(E/(F/G))", False],
                             ["C", None, False] ])
        
        apps = list(applications_per_slash_with_path(catseq, 6))
        self.assertEqual(["fwd_comp",
                      "fwd_appl",
                      None,
                      None,
                      None,
                      None], apps)
    
    
    def test_by_slash3(self):
        # slash index:              4  3  2  1  0
        catseq = self.build_seq([ ["((((a/b)/c)/d)/e)/f", None, False],
                             ["g/(g\\(((((a/b)/c)/d)/e)/f))", ",", False],
                             ["g/(g\\(((((a/b)/c)/d)/e)/f))", "g\\(((((a/b)/c)/d)/e)/f)", False],
                             ["g", None, False] ])
        apps = list(applications_per_slash_with_path(catseq, 5))
        self.assertEqual([ None, None, None, None, None
                     ], apps)
    
    
    def test_by_slash4(self):
        catseq = self.build_seq([ ["a/b", None, False],
                             ["t/(t\\(a/b))", None, False] ])
        apps = list(applications_per_slash_with_path(catseq, 1))
        self.assertEqual([ None ], apps)
    
    
    def test_by_slash5(self):
        catseq = self.build_seq([ ["a/b", ",", False],
                             ["a/b", None, False] ])
        apps = list(applications_per_slash_with_path(catseq, 1))
        # Defines comma absorption as consuming the slash (although it doesn't)
        self.assertEqual([None], apps)
    
    
    def test_by_slash6(self):
        # slash index                   2  1  0  3
        catseq = self.build_seq([ ["((a\\b)/b)/(c/d)", "c/d", False ],
                             ["(a\\b)/b", "b", False ],
                             ["b", "a\\b", True],
                             ["a", None, False] ])
        apps = list(applications_per_slash_with_path(catseq, 4))
        self.assertEqual([ "fwd_appl", "fwd_appl", "bwd_appl", None ], apps)
    
