import unittest

from apps.cn.mkdeps import mkdeps, UnificationException
from apps.cn.mkmarked import naive_label_derivation
from munge.ccg.parse import parse_tree

def parse_gsdeps(line):
    return set(tuple(dep.split('|')) for dep in line.split())

class DepTests(unittest.TestCase):
    def check(self, derivs_file, gs_file):
        with open(derivs_file) as f:
            with open(gs_file) as gs:
                file = f.readlines()
                gsdeps_file = gs.readlines()
            
                while file and gsdeps_file:
                    _, deriv = file.pop(0), file.pop(0)
                    gsdeps_line = gsdeps_file.pop(0)
                    
                    if deriv.startswith('#'): continue
                    
                    t = naive_label_derivation(parse_tree(deriv))
                    deps = mkdeps(t)
                    gsdeps = parse_gsdeps(gsdeps_line)
                    
                    try:
                        self.assertEqual(deps, gsdeps)
                    except AssertionError:
                        print "EXPECTED\n-------"
                        for depl, depr in sorted(gsdeps):
                            print depl, depr
                        print "GOT\n---"
                        for depl, depr in sorted(deps):
                            print depl, depr
                        print "DIFF\n----"
                        print "false negatives: %s" % ' '.join('|'.join((u, v)) for u, v in list(set(gsdeps) - set(deps)))
                        print "false positives: %s" % ' '.join('|'.join((u, v)) for u, v in list(set(deps) - set(gsdeps)))
                            
                        raise
        
    def testBasic(self):
        self.check('apps/cn/tests/test1.ccg', 'apps/cn/tests/test1.gs')
        self.check('apps/cn/tests/test2.ccg', 'apps/cn/tests/test2.gs')
        self.check('apps/cn/tests/test3.ccg', 'apps/cn/tests/test3.gs')
#        self.check('final/chtb_9992.fid', 'apps/cn/tests/blah.gs')
                    
if __name__ == '__main__':
    unittest.main()