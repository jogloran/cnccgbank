class CountDict(dict):
    '''Accessing a non-existent key in this dictionary will return the value zero.'''

    def __missing__(self, key):
        return 0

def sorted_by_value_desc(dict):
    '''Given a _dict_, returns its (key, value) pairs sorted in descending order.'''
    return sorted(dict.iteritems(), key=lambda (k, v): v, reverse=True)

def smash_key_case(d):
    '''Given a dictionary _d_, lowercases its keys.'''
    return dict( (k.lower(), v) for (k, v) in d.iteritems() )