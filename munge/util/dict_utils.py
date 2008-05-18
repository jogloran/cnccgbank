class CountDict(dict):
    '''Accessing a non-existent key in this dictionary will return the value zero.'''

    def __missing__(self, key):
        return 0

def sorted_by_value_desc(hash):
    return sorted(hash.iteritems(), key=lambda (k, v): v, reverse=True)
