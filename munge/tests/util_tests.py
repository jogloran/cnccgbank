import unittest
from munge.util.iter_utils import flatten

class UtilTests(unittest.TestCase):
    def testFlatten(self):
        self.assertEquals(flatten( (1, (2, (3, (4, (5, 6))))) ), (1, 2, 3, 4, 5, 6))
        self.assertEquals(flatten( () ), () )
        self.assertEquals(flatten( (1, 2, 3, 4) ), (1, 2, 3, 4))

    def test_first_index_such_that(self):
        l = [3, 5, 7, 9, 10, 11]
        i = first_index_such_that(lambda e: e % 2 == 0, l)
        self.assertEquals(i, 4)

        j = last_index_such_that(lambda e: e % 2 == 0, l)
        self.assertEquals(j, 1)

        k = first_index_such_that(lambda e: e > 15, l)
        self.assert_(k is None)

        m = last_index_such_that(lambda e: e > 15, l)
        self.assert_(m is None)

    def testFind(self):
        l = [4, 6, "s", 10, 11, 12, 14]
        self.assertEqual(find(lambda e: e % 2 != 0, l), 11)
        self.assert_(find(lambda e: e > 15) is None)
        
    def testStarmap(self):
        def f(a, b, c):
            return a + b + c

        tuple = ( (1, 2, 3), (10, 15, 30) )
        self.assertEquals(starmap(f, l), (6, 55))

    def testSublist(self):
        smaller = ()
        larger = (1, 2, 3)
        self.assert_(is_sublist(smaller, larger))

        smaller = (1, 2, 3)
        larger = (4, 5, 1, 2, 3, 4)
        self.assert_(is_sublist(smaller, larger))
        larger = (4, 5, 1, 2, 3)
        self.assert_(is_sublist(smaller, larger))
        larger = (4, 5, 6, 7)
        self.assertFalse(is_sublist(smaller, larger))
        larger = (4, 5, 6, 1, 2, 7)
        self.assertFalse(is_sublist(smaller, larger))

    def test_each_pair(self):
        pairs = list(each_pair(range(3)))
        self.assertEquals(pairs, [ (0, 1), (1, 2) ])
        
        pairs = list(each_pair( () ))
        self.assertFalse(pairs)

        pairs = list(each_pair(range(100)))
        self.assertEquals(len(pairs), 99)

    def testReject(self):
        l = range(10)
        list = reject(l, lambda e: e % 2 == 0)
        self.assertFalse( any(lambda e: e % 2 == 0, list) )

    def testCountDict(self):
        c = CountDict()
        c['test'] += 1
        self.assertEquals(c['test'], 1)

        self.assertEquals(c['foo'], 0)

        c['test'] += 1
        self.assertEquals(c['test'], 2)

