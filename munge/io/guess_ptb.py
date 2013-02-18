# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.penn.io import AugmentedPTBReader
from munge.penn.prefaced_io import PrefacedPTBReader
from munge.penn.yz_io import YZPTBReader
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
    # 41 bytes are needed if the derivation number can enter 3 digits
    # e.g. "ID=wsj_1068.153 PARSER=GOLD NUMPARSE=1\n((" = 41 bytes
    @staticmethod
    def bytes_of_context_needed(): return 41
    
    @staticmethod
    def identify(context):
        return re.match(r'''ID=wsj_\d{4}.\d+ PARSER=GOLD NUMPARSE=1\n\(\(''', context) is not None
        
    @staticmethod
    def reader_class(): return PrefacedPTBReader

class YZPTBGuesser(object):
    @staticmethod
    def bytes_of_context_needed(): return 100
    
    @staticmethod
    def identify(context):
        return re.match(r'\( [^ ]+ [lrsec]', context)
        
    @staticmethod
    def reader_class(): return YZPTBReader