# (C) 2010 by Florian Mayer.

import inspect

magic = set(('__int__',))

def oldstyle(self, name, attr):
    if name in magic:
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
            object.__setattr__(self, name, attr)


class A(object):
    __setattr__ = oldstyle
    
    def __int__(self):
        return 2


a = A()
print int(a)
a.__int__ = lambda: 5
print int(a)

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
b.__int__ = lambda: 5
print int(b)
