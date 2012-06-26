import operator
import math
import sys
import random

random.seed(24601)

from munge.proc.filter import Filter
from munge.trees.traverse import leaves
from munge.util.err_utils import msg
from collections import namedtuple, defaultdict

Split = namedtuple('Split', ['train', 'test'])
def train_and_test_for_fold(derivs, k, n):
    '''Gets fold _k_ out of _n_ of the array _derivs_.'''
    fold_size = int(math.ceil(len(derivs)/float(n)))
    return Split(
            test =derivs[k*fold_size    :(k+1)*fold_size],
            train=derivs[               :(k-1)*fold_size] +
                  derivs[(k+1)*fold_size:               ])

def get_coverage(train, test, selector, mode):
    train_toks = set(selector(tok) for tok in train)

    if mode == 'type':
        test_toks  = set(selector(tok) for tok in test)
        test_toks_unseen_in_train = test_toks - train_toks
    elif mode == 'token':
        test_toks  = [selector(tok) for tok in test]
        test_toks_unseen_in_train = [tok for tok in test_toks if tok not in train_toks]
    else:
        raise ValueError('expected mode=type|token')

    return 1.0 - (len(test_toks_unseen_in_train) / float(len(test_toks)))

def avg(l):
    return sum(l) / float(len(l))

class CheckCoverage(Filter):
    NFOLDS = 10

    def __init__(self):
        Filter.__init__(self)
        self.words = []

    def accept_derivation(self, bundle):
        self.words += [
                (
                    e.lex,
                    str(e.cat),
#                    e.tag
                ) for e in leaves(bundle.derivation) ]

    def output(self):
        random.shuffle(self.words)

        self.coverages = defaultdict(list)
        for i in xrange(self.NFOLDS):
            split = train_and_test_for_fold(self.words, i, self.NFOLDS)
            for coverage_type, selector in (
                    ('category', operator.itemgetter(1)),
                    ('lex'     , operator.itemgetter(0))):
                #msg('Computing %s coverage for fold %d', coverage_type, i)
                for mode in ('type', 'token'):
                    self.coverages[coverage_type + '.' + mode].append(
                            get_coverage(train=split.train, test=split.test, selector=selector, mode=mode) )

        for coverage_type, coverages in self.coverages.iteritems():
            msg('%s: %.2f%%', coverage_type, avg(coverages) * 100.0)

