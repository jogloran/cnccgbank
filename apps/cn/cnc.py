from munge.proc.filter import Filter
from apps.cn.output import *
from munge.trees.traverse import leaves
from apps.identify_lrhca import base_tag

class PipeFormat(Filter, OutputDerivation):
    '''Generates the "piped" output format used by C&C.'''
    def __init__(self, outdir, format):
        Filter.__init__(self)
        OutputDerivation.__init__(self, transformer=self.transformer, outdir=outdir)
        
        self.format_string = self.make_format_string_from(format)
        
    def accept_derivation(self, bundle):
        self.write_derivation(bundle)
        
    def transformer(self, bundle):
        return " ".join(self.format(leaf) for leaf in leaves(bundle.derivation))
    
    @staticmethod
    def make_format_string_from(format):
        substitutions = {
            "%w": "%(lex)s",
            "%P": "%(stemmed_pos)s",
            "%p": "%(pos)s",
            "%s": "%(cat)s"
        }
        for src, dst in substitutions.iteritems():
            format = re.sub(src, dst, format)
        return format
        
    def format(self, leaf):
        return self.format_string % {'lex': leaf.lex, 'pos': leaf.pos1, 'cat': str(leaf.cat), 'stemmed_pos': base_tag(leaf.pos1)}
        
    opt = 'C'
    long_opt = 'pipe-format'
    
    arg_names = 'OUTDIR FORMAT-STRING'
