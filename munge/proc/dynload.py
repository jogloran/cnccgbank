import munge # Required to use the qualified name munge.proc.trace.Filter (just 'Filter' doesn't work)
from types import ClassType

def get_available_filters(loaded_modules):
    filters_found = []
    
    for module in loaded_modules:    
        for symbol_name in dir(module):
            #if not symbol_name[0].isalpha() or symbol_name[0].islower(): continue
            obj = getattr(module, symbol_name)
            
            if (type(obj) is type(ClassType) and issubclass(obj, munge.proc.trace.Filter) and
                obj is not munge.proc.trace.Filter):
                filters_found.append(obj)
    
    return filters_found
    
def get_available_filters_dict(loaded_modules):
    filters_found = {}
    
    for module in loaded_modules:    
        for symbol_name in dir(module):
            #if not symbol_name[0].isalpha() or symbol_name[0].islower(): continue
            obj = getattr(module, symbol_name)
            
            if (type(obj) is type(ClassType) and issubclass(obj, munge.proc.trace.Filter) and
                obj is not munge.proc.trace.Filter):
                filters_found[symbol_name] = obj
                # TODO: warn or error if key is already in hash
    
    return filters_found

def load_requested_packages(module_names):
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