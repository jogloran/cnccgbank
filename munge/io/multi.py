import os, re
from glob import glob
from munge.io.guess import GuessReader
from munge.util.err_utils import warn, info

class MultiGuessReader(object):
    '''A read-only reader which iterates over an entire PTB-structured corpus (one whose directory
hierarchy is corpus -> section+ -> document+). This reader allows neither index-based retrieval or
modification of derivations, nor corpus output.'''
    def __init__(self, topdir, reader=GuessReader, verbose=True):
        self.topdir = topdir
        _, tail = os.path.split(self.topdir)
        if re.match(r'\d\d', tail):
            self.sections = [self.topdir]
        else:
            self.sections = glob(os.path.join(self.topdir, '*'))
        self.reader = reader

        self.verbose = verbose

    def __iter__(self):
        for section_path in filter(lambda dir_name: os.path.isdir(dir_name), self.sections):
            docs = glob(os.path.join(section_path, '*'))
            for doc_path in docs:
                if self.verbose: info("Processing %s...", doc_path)
                reader = self.reader(doc_path)
                for deriv_bundle in reader:
                    yield deriv_bundle

    def no_getitem_setitem(self, *args):
        raise NotImplementedError("get and setitem unavailable with PTBCorpusReader.")
    __getitem__ = __setitem__ = no_getitem_setitem

    def __str__(self):
        raise NotImplementedError("Cannot directly generate treebank with PTBCorpusReader.")

class DirFileGuessReader(object):
    '''Reader allowing the uniform treatment of directories and files.'''
    def __init__(self, path, verbose=True, reader_class=None):
        self.path = path
        self.verbose = verbose
        self.reader_class = reader_class

    def __iter__(self):
        path = self.path

        if not os.path.exists(path):
            # TODO: This doesn't skip the current file (can we do that from inside the iterator?)
            warn("%s does not exist, so skipping.", path)

        if self.reader_class:
            reader_arg = { 'reader': self.reader_class }
        else:
            reader_arg = {}
            
        if os.path.isdir(path):
            reader = MultiGuessReader(path, verbose=self.verbose, **reader_arg)
        elif os.path.isfile(path):
            if self.reader_class:
                reader = self.reader_class(path)
            else:
                reader = GuessReader(path)
        else:
            warn("%s is neither a file nor a directory, so skipping.", path)

        for deriv_bundle in reader:
            yield deriv_bundle

