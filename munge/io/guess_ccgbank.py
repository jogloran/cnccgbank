from munge.ccg.io import CCGbankReader, WritableCCGbankReader

class CCGbankGuesser(object):
    @staticmethod
    def bytes_of_context_needed(): return 1
    
    @staticmethod
    def identify(context):
        return context[0] == 'I'
        
    @staticmethod
    def reader_class(): return CCGbankReader

class WritableCCGbankGuesser(CCGbankGuesser):
    @staticmethod
    def reader_class(): return WritableCCGbankReader