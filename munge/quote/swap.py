from munge.trees.traverse import get_leaf

class SwapComma(object):
    @staticmethod
    def process_punct(deriv, node, at):
        return get_leaf(deriv, at + 1, "backwards")