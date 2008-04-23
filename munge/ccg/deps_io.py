class DepRow(object):
    def __init__(self, *fields):
        self.fields = list(fields)
        self.fields[0] = int(self.fields[0])
        self.fields[1] = int(self.fields[1])
        
    def __str__(self):
        return '\t'.join(str(e) for e in self.fields)
        
    __repr__ = __str__
    
class Dep(object):
    def __init__(self, dep_rows=None, header=''):
        self.header = header
        self.dep_rows = dep_rows or []
    
    def __str__(self):
        s = self.header + "\n"
        s += "\n".join(str(row) for row in self.dep_rows)
        s += "\n<\\s>"
        return s
        
    def append(self, row):
        self.dep_rows.append(row)
        
    def __iter__(self):
        for row in self.dep_rows: yield row

class CCGbankDepsReader(object):
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
        
    def __iter__(self):
        IN_DERIV, OUTSIDE_DERIV = 1, 2
        state = OUTSIDE_DERIV
        
        cur = Dep()
        
        for line in self.file:
            line = line.rstrip()
            
            if line.startswith('<s'):
                state = IN_DERIV
                cur.header = line
                
            elif line.startswith(r'<\s'):
                state = OUTSIDE_DERIV
                yield cur
                
                del cur
                cur = Dep()
            else:
                if state == IN_DERIV:
                    cur.append( DepRow(*line.split()) )
                else:
                    pass