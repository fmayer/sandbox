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

class CachedGetattr(type):
    @staticmethod
    def wrap_getattr(gattr):
        def _fun(self, name):
            tmp = gattr(self, name)
            setattr(self, name, tmp)
            return tmp
        return _fun
    
    def __new__(mcls, name, bases, dct):
        dct['__getattr__'] = mcls.wrap_getattr(dct['__getattr__'])
        return type.__new__(mcls, name, bases, dct)


class Foo(object):
    __metaclass__ = CachedGetattr
    def __getattr__(self, name):
        return 'name'


f = Foo()
print dir(f)
print f.a
print dir(f)
