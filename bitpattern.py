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

import itertools

def conv_dec(number, base):
    ret = ''
    while number:
        nmb = number % base
        ret += str(nmb)
        number = (number - nmb) / base
    return ret[::-1]


def bitrange(start, stop):
    return ((1 << stop) - 1) ^ ((1 << start) - 1)


class BitSet(object):
    def __init__(self, bitgroups=None):
        self.compiled = []
        if bitgroups is not None:
            for size in bitgroups:
                self.add_bitgroup(size)
    
    def add_bitgroup(self, size):
        if self.compiled:
            offset = self.compiled[-1][0] + self.compiled[-1][1]
        else:
            offset = 0
        self.compiled.append((offset, size))
    
    def unpack_one(self, data, n):
        offset, size = self.compiled[n]
        bitmap = bitrange(offset, offset + size)
        return (data & bitmap) >> offset
    
    def unpack(self, data):
        for offset, size in self.compiled:
            bitmap = bitrange(offset, offset + size)
            yield (data & bitmap) >> offset
    
    def pack(self, values, checked=True):
        data = 0
        for n, (value, comp) in enumerate(
            itertools.izip_longest(values, self.compiled)):
            # This is done so we can accept any iterator without needing
            # to check for the length in advance.
            if value is None or comp is None:
                raise ValueError("Invalid number of values for bitset.")
            offset, size = comp
            if checked and len(conv_dec(value, 2)) > size:
                raise OverflowError(
                    "Value %r too long for %d bit(s) (bitgroup %d)."
                    % (value, size, n)
                )
            data |= value << offset
        return data
    
    def join(self, sdata, size):
        offset = data = 0
        for item in sdata:
            data |= item << offset
            offset += size
        return data
    
    def split(self, data, size):
        totalsize = sum(item[1] for item in self.compiled)
        curitem = 0
        while totalsize > 0:
            bitset = bitrange(curitem, curitem + min(size, totalsize))
            yield (data & bitset) >> curitem
            totalsize -= size
            curitem += size
    
    def tobytes(self, data):
        return ''.join(chr(item) for item in self.split(data, 8))
    
    def frombytes(self, sdata):
        return self.join((ord(x) for x in sdata), 8)


if __name__ == '__main__':
    p = BitSet([1, 4, 8])
    print p.pack([1, 3, 2])
    print list(p.unpack(p.pack([1, 3, 2])))
    print repr(p.tobytes(p.pack([1, 3, 2])))
    print list(p.split(p.pack([1, 3, 2]), 4))
    print p.tobytes(p.pack([1, 3, 2]))
    print p.frombytes(p.tobytes(p.pack([1, 3, 2]))) 
    assert p.pack([1, 3, 2]) == p.frombytes(p.tobytes(p.pack([1, 3, 2])))
    assert p.pack([1, 3, 2]) == p.join(p.split(p.pack([1, 3, 2]), 4), 4)
