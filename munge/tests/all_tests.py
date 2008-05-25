import unittest
from munge.tests.penn_parse_tests import PennParseTests
from munge.tests.penn_tests import PennTests
from munge.tests.parse_tests import ParseTests
from munge.tests.lex_tests import LexTests
from munge.tests.ccg_tests import CCGTests
from munge.tests.cat_tests import CatTests
from munge.tests.trace_tests import TraceTests
from munge.tests.util_tests import UtilTests
from munge.tests.tgrep_tests import TgrepTests

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass
    
    for test_case in (PennParseTests, PennTests, ParseTests, 
					  LexTests, CCGTests, CatTests, TraceTests, UtilTests, TgrepTests):
        unittest.TestLoader().loadTestsFromTestCase(test_case)

    unittest.main()
