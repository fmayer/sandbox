# (C) 2010 by Florian Mayer

import math
import ctypes
import ctypes.util

cmath = ctypes.cdll.LoadLibrary(ctypes.util.find_library('m'))
prot = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_double)


def genlog(loge):
    if hasattr(math, loge):
        return getattr(math, loge)
    elif hasattr(cmath, loge):
        return prot((loge, cmath))
    else:
        if not loge.startswith('log'):
            raise ValueError
        
        e = int(loge[3:])
        return lambda n: math.log(n, e)


class Wrap(object):
    def __getattr__(self, name):
        if name.startswith('log'):
            fun = genlog(name)
            setattr(self, name, fun)
            return fun
        
        return super(Wrapper, self).__getattr__(name)
    
    def log(self, n):
        return getattr(self, 'log' + n)


#: To be used as `from genlog import wrap as mlog` or equivalent.
#: Then mlog can be used to obtain arbitrary logarithmic functions.
wrap = Wrap()
