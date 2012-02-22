# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

# Signals error states when parsing string representations.
class DocParseException(Exception): pass

class PennParseException(DocParseException): pass
class CCGbankParseException(DocParseException): pass
class CPTBParseException(DocParseException): pass
class CatParseException(DocParseException): pass

class TgrepException(Exception): pass
class MungeException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self): return self.msg

class FilterException(Exception):
    def __init__(self, inner, context, msg=''):
        Exception.__init__(self)
        self.inner = inner
        self.context = context
        self.msg = msg