from munge.io.multi import DirFileGuessReader
from itertools import izip
from munge.util.err_utils import info

class Derivation(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def label(self):
        return "%s/%s" % (self.left.label(), self.right.label())
        
    @property
    def derivation(self):
        return (self.left.derivation, self.right.derivation)

class PairedReader(object):
    @staticmethod
    def parse_dirspec(dirspec):
        return dirspec.split('~', 2)
        
    def __init__(self, dirspec, verbose, reader_class=DirFileGuessReader):
        self.leftdir, self.rightdir = self.parse_dirspec(dirspec)
        self.verbose = verbose
        self.reader = reader_class
        
    def __iter__(self):
        for left, right in izip(self.reader(self.leftdir), self.reader(self.rightdir)):
            info("Processing %s/%s", left.label(), right.label())
            deriv = Derivation(left, right)
            yield deriv
            
            del deriv
            del left
            del right