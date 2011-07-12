from munge.util.str_utils import padded_rsplit

class SingleReader(object):
    '''The SingleReader mix-in allows a filename containing a trailing index :N
to identify a single derivation within a given document.'''

    def derivation_with_index(self, filename, i):
        '''Overridden by subclasses, this should return a parsed object for
the derivation with index _i_ inside _filename_.'''
        raise NotImplementedError('derivation_with_index must be overridden.')
        
    @staticmethod
    def get_offset(filename):
        return padded_rsplit(filename, ':', 1)
        
    def __init__(self, filename):
        '''SingleReader subclasses have the instance variable _index_ containing
the selected index, and _derivs_, which is either an array containing the selected
derivation, or all derivations if no index was provided. '''
        filename, index = self.get_offset(filename)
        if index: index = int(index)
        
        if index:
            self.derivs = self.derivation_with_index(filename, index)
        else:
            self.derivs = self.derivation_with_index(filename)
            
        self.filename = filename
        self.index = index
