# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.trees.traverse import text

class Tokens(Filter):
    def __init__(self, outfile):
        if isinstance(outfile, basestring):
            self.outfile = outfile
            self.f = file(self.outfile, 'w')
        elif isinstance(outfile, file):
            self.f = outfile
            self.outfile = outfile.name
        else:
            raise FilterException, "Expected filename or file object."
    
    def accept_derivation(self, deriv):
        print >>self.f, "%s|%s" % (deriv.label(), ' '.join(deriv.derivation.text()))
        
import sys
class PrintTokens(Tokens, Filter):
    def __init__(self):
        Tokens.__init__(self, sys.stdout)
        
    opt = "t"
    long_opt = "tokens"
    
class PrintQuoted(Filter):
    def __init__(self, outfile):
        if isinstance(outfile, basestring):
            self.outfile = outfile
            self.f = file(self.outfile, 'w')
        elif isinstance(outfile, file):
            self.f = outfile
            self.outfile = outfile.name
        else:
            raise FilterException, "Expected filename or file object."
            
    def accept_derivation(self, deriv):
        text = list(leaves(deriv.derivation))
        if any(map(lambda token: token.lex in ("``", "`", "''", "'") and token.pos1 != "POS", text)):
            print >>self.f, "%s|%s" % (deriv.label(), ' '.join(deriv.derivation.text()))
            
    opt = '"'
    long_opt = "dump-quoted"
