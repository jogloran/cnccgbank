from types import TypeType

import munge # Required to use the qualified name munge.proc.trace.Filter (just 'Filter' doesn't work)
from munge.util.err_utils import warn

def get_available_filters_dict(loaded_modules):
    '''Given a list of module objects, returns a dictionary mapping from filter names to valid 
filter objects found in those modules' namespaces.'''
    
    filters_found = {}
    
    for module in loaded_modules:
        for symbol_name in dir(module):
            obj = getattr(module, symbol_name)
            
            # Only consider classes which are strict subclasses of Filter
            if (type(obj) is TypeType and issubclass(obj, munge.proc.trace.Filter) and
                obj is not munge.proc.trace.Filter):
                if symbol_name in filters_found:
                    warn("An already loaded filter with the name %s has been overwritten by a filter with the same name.", symbol_name)
                    
                filters_found[symbol_name] = obj
    
    return filters_found

def load_requested_packages(module_names):
    '''Tries to load each module named in _module_names_, returning an array of the loadable module objects found in that module names.'''
    loaded_modules = []
    
    for module in module_names:
        try:
            # Suppose we want to import A.B.C. When fromlist is anything but [], it returns A.B.C.
            # Otherwise, it returns the topmost module, A.
            loaded_modules.append( __import__(module, fromlist=[module]) )
        except ImportError, e:
            warn("Couldn't import module %s (%s)", module, e)
            
    return loaded_modules
    
def get_argcount_for_method(method):
    '''Returns the number of arguments (excluding implicit self) expected by the given instance method.
    Assumes that _method_ is an instance and not a class or static method.'''
    return method.im_func.func_code.co_argcount - 1
