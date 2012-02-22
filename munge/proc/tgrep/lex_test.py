# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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