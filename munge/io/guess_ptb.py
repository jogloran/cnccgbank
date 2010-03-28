from munge.penn.io import AugmentedPTBReader

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
