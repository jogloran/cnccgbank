class CountDict(dict):
    '''Accessing a non-existent key in this dictionary will return the value zero.'''

    def __missing__(self, key):
        return 0
