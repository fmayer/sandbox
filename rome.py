# (C) 2009 by Florian Mayer

roman_numbers = (
    ('M',  1000), ('CM', 900), ('D',  500),
    ('CD', 400), ('C',  100), ('XC', 90),
    ('L',  50), ('XL', 40), ('X',  10), 
    ('IX', 9), ('V',  5), ('IV', 4), ('I',  1)
)

class Roman(object):
    def __init__(self, num=None, value=None):
        self.value = 0
        
        self.num = num
        if value is not None:
            self.value = value
        else:
            while num:
                for r, n in roman_numbers:
                    if num.startswith(r):
                        self.value += n
                        num = num[len(r):]
    
    @classmethod
    def from_value(cls, number):
        temp = ""
        for numeral, integer in roman_numbers:
            div, mod = divmod(number, integer)
            if div != 0:
                temp += div * numeral
                number = mod
        return cls(temp, number)
    
    @staticmethod
    def _to_number(other):
        if isinstance(other, basestring):
            return Roman(other).value
        elif isinstance(other, (int, long)):
            return other
        elif isinstance(other, Roman):
            return other.value
        else:
            raise NotImplementedError
    
    def __div__(self, other):
        return Roman.from_value(self.value / self._to_number(other))
    
    def __add__(self, other):
        return Roman.from_value(self.value + self._to_number(other))
        
    def __sub__(self, other):
        return Roman.from_value(self.value - self._to_number(other))
        
    def __mul__(self, other):
        return Roman.from_value(self.value * self._to_number(other))
    
    def __rdiv__(self, other):
        return Roman.from_value(self._to_number(other) / self.value)
    
    def __radd__(self, other):
        return Roman.from_value(self._to_number(other) + self.value)
        
    def __rsub__(self, other):
        return Roman.from_value(self._to_number(other) - self.value)
        
    def __rmul__(self, other):
        return Roman.from_value(self._to_number(other) * self.value)
    
    def __repr__(self):
        return self.num
    
    __str__ = __repr__


if __name__ == '__main__':
    print 3 + Roman("III")
    print Roman("V") + Roman("X")
    print Roman("V") + 3
