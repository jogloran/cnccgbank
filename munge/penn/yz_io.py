from munge.penn.io import PTBReader
from munge.penn.parse import YZPTBParser, parse_tree

class YZPTBReader(PTBReader):
    def __init__(self, *args):
        PTBReader.__init__(self, *args)

    @staticmethod
    def parse_file(text):
        return parse_tree(text, YZPTBParser)