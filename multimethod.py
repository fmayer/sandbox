# Copyright (c) 2011 Florian Mayer <florian.mayer@bitsrc.org>

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

from itertools import izip

class MultiMethod(object):
    def __init__(self, get):
        self.get = get
        
        self.methods = []
        self.cache = {}
    
    def add(self, fun, types):
        self.cache = {}
        self.methods.append((types, fun))
    
    def add_dec(self, *types):
        self.cache = {}
        def _dec(fun):
            self.methods.append((types, fun))
            return fun
        return _dec
    
    def get_item(self, objs):
        types = tuple(map(type, objs))
        cached = self.cache.get(types, None)
        if cached is not None:
            return cached
        
        for signature, fun in reversed(self.methods):
            if all(isinstance(*x) for x in izip(objs, signature)):
                self.cache[types] = fun
                return fun
        raise TypeError
    
    def get_superitem(self, objs):
        types = tuple(map(type, objs))
        cached = self.cache.get(types, None)
        if cached is not None:
            return cached
        
        for signature, fun in reversed(self.methods):
            for obj, cls in izip(objs, signature):
                print obj, objs
                if isinstance(obj, super):
                    thiscls = obj.__thisclass__
                    n = 1
                else:
                    thiscls = obj.__class__
                    n = 0
                if not issubclass(thiscls.__mro__[n], cls):
                    break
            else:
                self.cache[types] = fun
                return fun
        raise TypeError
    
    def __call__(self, *args, **kwargs):
        obj = self.get(*args, **kwargs)
        return self.get_item(obj)(*args, **kwargs)
    
    def super(self, *args, **kwargs):
        obj = self.get(*args, **kwargs)
        fun = self.get_superitem(obj)
        
        nargs = []
        for elem in args:
            if isinstance(elem, super):
                nargs.append(elem.__self__)
            else:
                nargs.append(elem)
        
        for k in kwargs:
            if isinstance(kwargs[k], super):
                kwargs[n] = kwargs[k].__self__
        
        return fun(*nargs, **kwargs)


if __name__ == '__main__':
    class String(str):
        pass
    
    mm = MultiMethod(lambda *a: a)
    
    @mm.add_dec(str, str)
    def foo(foo, bar):
        return 'String', foo, bar
    
    @mm.add_dec(String, str)
    def foo(foo, bar):
        return 'Fancy', foo, bar, mm.super(super(String, foo), bar)
        
    @mm.add_dec(int, str)
    def foo(foo, bar):
        return 'Int - String', foo, bar
    
    print mm('foo', 'bar')
    print mm(1, 'bar')
    print mm(1, 'bar')
    print mm('foo', 'bar')
    
    @mm.add_dec(int, int)
    def foo(foo, bar):
        return foo + bar
    
    print mm('foo', 'bar')
    print mm(1, 2)
    
    print mm(String('foo'), 'bar')
