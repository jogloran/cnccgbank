from munge.cptb.io import CPTBReader

class CPTBGuesser(object):
    @staticmethod
    def bytes_of_context_needed(): return 1
    
    @staticmethod
    def identify(context):
        return context[0] == '<'
        
    @staticmethod
    def reader_class(): return CPTBReader
