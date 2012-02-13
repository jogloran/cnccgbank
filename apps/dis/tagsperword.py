from apps.util.tabulation import Tabulation
from munge.proc.filter import Filter
from munge.trees.traverse import nodes

class TagsPerWord(Tabulation('tags_per_word', reducer=len, value_maker=set, limit=10), Filter):
    def __init__(self):
        super(TagsPerWord, self).__init__()
        
    def accept_leaf(self, leaf):
        self.tags_per_word[leaf.lex].add( str(leaf.cat) )
        
    def output(self):
        super(TagsPerWord, self).output()
        avg = (sum(len(v) for v in self.tags_per_word.values()) / 
               float(len(self.tags_per_word.keys())))
        print "avg. tags per word: %.2f" % avg

class UnariesPerSentence(Filter):
    def __init__(self):
        self.unaries = 0
        self.nsents = 0

    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.count() == 1: self.unaries += 1
        self.nsents += 1

    def output(self):
        print 'avg #unaries/sentence = %d/%d = %.2f%%' % (self.unaries, self.nsents, self.unaries/float(self.nsents)*100.)
