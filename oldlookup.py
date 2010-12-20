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

import inspect

forbidden = set(('__setattr__', '__class__'))

def is_magic(name):
    return (
        name not in forbidden and name.startswith('__') and name.endswith('__')
    )


def oldstyle(self, name, attr):
    if is_magic(name):
        d = dict(self.__class__.__dict__)
        d.update({name: staticmethod(attr)})
        ncls = type(
            self.__class__.__name__ + 'Magic', self.__class__.__bases__, d)
        
        self.__class__ = ncls
    else:
        
        if (not inspect.ismethod(self.__setattr__) or
            self.__setattr__.im_func != oldstyle):
            # Costum setattr is stored in the instance so that this method is
            # never overriden. Hence __setattr__ is not part of the global
            # magic set.
            self.__setattr__(name, attr)
        else:
            super(self.__class__, self).__setattr__(name, attr)


if __name__ == '__main__':
    class A(object):
        __setattr__ = oldstyle
        
        def __int__(self):
            return 2
    
    
    a = A()
    print int(a)
    assert int(a) == 2
    a.__int__ = lambda: 5
    print int(a)
    assert int(a) == 5
    
    def sattr(name, attr):
        print name, attr
    
    
    a.__setattr__ = sattr
    
    # Replace __setattr__ and verify it has an effect.
    print a.__setattr__
    a.b = 1
    
    print
    
    class B(object):
        def __int__(self):
            return 2
    
    
    b = B()
    print int(b)
    assert int(b) == 2
    b.__int__ = lambda: 5
    print int(b)
    assert int(b) == 2
