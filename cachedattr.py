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
