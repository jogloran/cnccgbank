from munge.io.guess_ptb import PTBGuesser
from munge.io.guess_cptb import CPTBGuesser
from munge.io.guess_ccgbank import CCGbankGuesser

class GuessReader(object):
    def __init__(self, filename, guessers=(CCGbankGuesser, PTBGuesser, CPTBGuesser), default=CCGbankGuesser):
        self.guessers = list(guessers)
        self.default = default
        
        self.preview = open(filename, 'r'
                ).read(max(guessers, key=lambda guesser: guesser.bytes_of_context_needed()
                ).bytes_of_context_needed())

        self.reader_class = self.determine_reader(self.preview)
        self.reader = self.reader_class(filename)
        
    def determine_reader(self, preview):
        for guesser in self.guessers:
            if guesser.identify(preview):
                return guesser.reader_class()
        return self.default
        
    def __iter__(self):
        for deriv in self.reader: yield deriv
        
    def __getitem__(self, index):
        '''Delegates to the guessed reader's __getitem__ method.'''
        return self.reader.__getitem__(index)
        
    def __setitem__(self, index, value):
        '''Delegates to the guessed reader's __setitem__ method.'''
        return self.reader.__setitem__(index, value)

    @property
    def derivs(self):
        return self.reader.derivs
        
    def __str__(self):
        return self.reader.__str__()