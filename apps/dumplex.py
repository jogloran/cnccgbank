from munge.proc.filter import Filter

class DumpLex(Filter):
    def __init__(self):
        Filter.__init__(self)
        
    def accept_derivation(self, bundle):
        print bundle.label(), ' '.join(bundle.derivation.text())