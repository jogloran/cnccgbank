try:
    import ply.lex as lex
    import ply.yacc as yacc
except ImportError:
    import lex, yacc
    
from munge.util.err_utils import debug, info
import munge.proc.tgrep.parse as parse

if __name__ == '__main__':
    import sys
    lex.lex(module=parse)
    
    expr = sys.argv[1]
    debug("Lexing %s", expr)
    lex.input(expr)
    for tok in iter(lex.token, None):
        debug("%s %s", tok.type, tok.value)