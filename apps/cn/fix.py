from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, multi_tgrep
from apps.cn.output import *
from munge.util.dict_utils import smash_key_case

class Fix(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self)
        
        self.outdir = outdir
        
    def pattern(self):
        '''
        Defines how to dispatch to fix functions. Accepts:
        - an (unordered) hash, mapping tgrep expressions to fix functions
        - an (ordered) list of 2-tuples <expr, fix>
        - a string tgrep expression, all matches of which will be passed to 'fix'
        - an iterable, each element of which will be passed to 'fix'
        '''
        raise NotImplementedError('You must subclass FixExtraction to specify a pattern.')
        
    def fix(self, node):
        pass
        
    @staticmethod
    def do_tgrep_with_callback(root, pattern, callback):
        for match_node, context in tgrep(root, pattern, with_context=True):
            if context: # only supply a context if the expression binds variables
                # smash the case, variables in tgrep expressions are case insensitive
                callback(match_node, **smash_key_case(context))
            else:
                callback(match_node)
    
    @staticmethod
    def is_valid_pattern_and_callback_tuple(v):
        return len(v) == 2 and isinstance(v[0], basestring) and callable(v[1])
        
    def accept_derivation(self, bundle):
        pattern = self.pattern()
        
        if isinstance(pattern, dict):
            multi_tgrep(bundle.derivation, pattern)
            
        elif isinstance(pattern, list):
            for pattern_and_callback in pattern:
                if Fix.is_valid_pattern_and_callback_tuple(pattern_and_callback):
                    pattern, callback = pattern_and_callback
                    Fix.do_tgrep_with_callback(bundle.derivation, pattern, callback)
                    
        elif isinstance(pattern, basestring):
            Fix.do_tgrep_with_callback(bundle.derivation, pattern, self.fix)
            
        elif callable(pattern):
            try:
                iterator = iter(pattern(bundle.derivation))
                for match_node in iterator:
                    self.fix(match_node)
            except TypeError, e:
                raise TypeError('Functions passed as patterns must return an iterable: ' + str(e))
            
        else:
            raise TypeError('Pattern must be a { pattern: callback } dictionary or a pattern string.')
            
        self.write_derivation(bundle)