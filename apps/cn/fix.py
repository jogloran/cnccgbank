# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, multi_tgrep
from munge.util.dict_utils import smash_key_case
from munge.util.err_utils import debug

from apps.cn.output import OutputPrefacedPTBDerivation

class Fix(Filter, OutputPrefacedPTBDerivation):
    '''An abstract filter which matches against particular node configurations and dispatches to
a specified fix function to operate on that node. In addition, the output() method of this filter
writes the modified derivations out in the prefaced PTB style.'''
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
        
    def pattern(self):
        '''
        Defines how to dispatch to fix functions. Accepts:
        - an (unordered) hash, mapping tgrep expressions to fix functions
        - an (ordered) list of 2-tuples <expr, fix>
        - a string tgrep expression, all matches of which will be passed to 'fix'
        - an iterable, each element of which will be passed to 'fix'
        '''
        raise NotImplementedError('You must subclass Fix.pattern() to specify a pattern.')
        
    def fix(self, node):
        pass
        
    @staticmethod
    def do_tgrep_with_callback(root, pattern, callback, **kwargs):
        new_root = None
        for match_node, context in tgrep(root, pattern, with_context=True, **kwargs):
            debug("Callback %s matched", callback.__name__)
            if context: # only supply a context if the expression binds variables
                # smash the case, variables in tgrep expressions are case insensitive
                result = callback(match_node, **smash_key_case(context))
            else:
                result = callback(match_node)
                
            # a new root will be returned if one has been installed
            if result: new_root = result
        
        return new_root or root
    
    @staticmethod
    def is_valid_pattern_and_callback_tuple(v):
        return len(v) >= 2 and isinstance(v[0], basestring) and callable(v[1])
        
    def accept_derivation(self, bundle):
        pattern = self.pattern()
        
        # Unordered actions
        # { pattern1: action1, ... }
        if isinstance(pattern, dict):
            multi_tgrep(bundle.derivation, pattern)
        
        # Ordered actions    
        # [ (pattern1, action1), ... ]
        elif isinstance(pattern, list):
            for pattern_and_callback in pattern:
                if Fix.is_valid_pattern_and_callback_tuple(pattern_and_callback):
                    if len(pattern_and_callback) == 2:
                        pattern, callback = pattern_and_callback
                        kwargs = {}
                    elif len(pattern_and_callback) == 3:
                        pattern, callback, kwargs = pattern_and_callback
                        
                    bundle.derivation = Fix.do_tgrep_with_callback(bundle.derivation, pattern, callback, **kwargs)
        
        # A string tgrep expression            
        # "pattern": fix
        elif isinstance(pattern, basestring):
            bundle.derivation = Fix.do_tgrep_with_callback(bundle.derivation, pattern, self.fix)
            
        # Iterator over nodes
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