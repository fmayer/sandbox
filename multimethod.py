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
from warnings import warn
from itertools import izip

SILENT = 0
WARN = 1
FAIL = 2

def _fmt_t(types):
    return ', '.join(type_.__name__ for type_ in types)


def _fmt_ovr(override, types, signature):
    if override == FAIL:
        raise TypeError
    elif override == WARN:
        warn(
            'Definition (%s) overrides prior definition (%s).' %
            (_fmt_t(types), _fmt_t(signature)),
            stacklevel=4
        )
    else:
        raise ValueError('Invalid level for override')


class MultiMethod(object):
    def __init__(self, get):
        self.get = get
        
        self.methods = []
        self.cache = {}
    
    def add(self, fun, types, override=SILENT):
        if override:
            for signature, fun in self.methods:
                if all(issubclass(a, b) for a, b in izip(types, signature)):
                    _fmt_ovr(override, types, signature)
        self.methods.append((types, fun))
    
    def add_dec(self, *types, **kwargs):
        self.cache = {}
        def _dec(fun):
            self.add(fun, types, kwargs.get('override', SILENT))
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
                if isinstance(obj, super):
                    thiscls = obj.__thisclass__
                    if not issubclass(thiscls.__mro__[1], cls):
                        break
                else:
                    if not isinstance(obj, cls):
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
    
    @mm.add_dec(String, str, override=6)
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
