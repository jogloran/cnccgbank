import sys
import ply.lex as lex
import ply.yacc as yacc
import munge.ccg.nodes as ccg
from munge.cats.cat_defs import C
import munge.proc.tgrep.parse as parse
from munge.trees.traverse import nodes

tgrep_debug = False

def initialise():
    lex.lex(module=parse)
    yacc.yacc(module=parse)

def tgrep(deriv, expression):
    if tgrep_debug:
        lex.input(expression)
        for tok in iter(lex.token, None):
            print tok.type, tok.value

    query = yacc.parse(expression)
    return any(query.is_satisfied_by(node) for node in nodes(deriv))

from munge.proc.filter import Filter
class Tgrep(Filter):
    def __init__(self, expression):
        Filter.__init__(self)
        initialise()
        self.expression = expression

    def accept_derivation(self, derivation_bundle):
        if tgrep(derivation_bundle.derivation, self.expression):
            print derivation_bundle.label()

    opt = 't'
    long_opt = 'tgrep'
    arg_names = 'EXPR'

if __name__ == '__main__':
    l=sys.argv[1]
    lex.input(l)
    for tok in iter(lex.token, None):
        print tok.type, tok.value

    p = yacc.parse(sys.argv[1])

    t = ccg.Node(
            C('A'), 0,0, None, 
            ccg.Node(
                C('B'), 0, 0, None,
                ccg.Leaf(C('C'), 'pos', 'pos', 'C', 'C'), None
                ),
            ccg.Leaf(
                C('D'), 'pos', 'pos', 'D', 'D'
                )
            )
    print t
    print any(p.is_satisfied_by(node) for node in nodes(t))
