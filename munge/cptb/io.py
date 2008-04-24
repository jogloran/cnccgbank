from munge.penn.parse import parse_tree

class Derivation(object):
    def __init__(self, ):
        pass
    
class CPTBReader(object):
    def get_derivs_text(self, f):
        INSIDE, OUTSIDE = 1, 2
        derivs = []
        cur = ''
        state = OUTSIDE
        for line in f:
            if line.startswith('<P>'):
                state = INSIDE
            elif line.startswith('</P>'):
                state = OUTSIDE
                derivs.append(cur)
                cur = ''
            elif line.startswith('<'):
                continue
            else:
                cur += line.rstrip()
                
        derivs = map(lambda s: unicode(s, 'gb-2312'))
        return derivs
            
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        
        self.derivs_text = self.get_derivs_text(self.file)
        self.trees = parse_tree('\n'.join(self.derivs_text))