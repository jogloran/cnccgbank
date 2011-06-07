# Signals error states when parsing string representations.
class DocParseException(Exception): pass

class PennParseException(DocParseException): pass
class CCGbankParseException(DocParseException): pass
class CPTBParseException(DocParseException): pass
class CatParseException(DocParseException): pass

class FilterException(Exception):
    def __init__(self, inner, context, msg=''):
        Exception.__init__(self)
        self.inner = inner
        self.context = context
        self.msg = msg