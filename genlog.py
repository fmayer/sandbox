# Copyright (c) 2010 Florian Mayer <flormayer (at) aim (dot) com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import math
import ctypes
import ctypes.util

cmath = ctypes.cdll.LoadLibrary(ctypes.util.find_library('m'))
prot = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_double)


def genlog(loge):
    if hasattr(math, loge):
        return getattr(math, loge)
    elif hasattr(cmath, loge):
        prt = prot((loge, cmath))
        def _fun(x):
            try:
                return prt(x)
            except ctypes.ArgumentError:
                e = int(loge[3:])
                return math.log(n, e)
        
        return _fun
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
        return getattr(self, 'log' + str(n))


#: To be used as `from genlog import wrap as mlog` or equivalent.
#: Then mlog can be used to obtain arbitrary logarithmic functions.
wrap = Wrap()
