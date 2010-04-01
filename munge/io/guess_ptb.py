from munge.penn.io import AugmentedPTBReader
from munge.penn.prefaced_io import PrefacedPTBReader
import re

class PTBGuesser(object):
    @staticmethod
    def bytes_of_context_needed(): return 3
    
    @staticmethod
    def identify(context):
        for char in context:
            if not char.isspace() and char == '(': return True
        
        return False
        
    @staticmethod
    def reader_class(): return AugmentedPTBReader

class PrefacedPTBGuesser(object):
    @staticmethod
    def bytes_of_context_needed(): return 40
    
    @staticmethod
    def identify(context):
        return re.match(r'''ID=wsj_\d{4}.\d+ PARSER=GOLD NUMPARSE=1\n\(\(''', context) is not None
        
    @staticmethod
    def reader_class(): return PrefacedPTBReader
