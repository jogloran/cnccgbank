# Signals error states when parsing string representations.
class DocParseException(Exception): pass

class PennParseException(DocParseException): pass
class CCGbankParseException(DocParseException): pass
class CatParseException(DocParseException): pass
