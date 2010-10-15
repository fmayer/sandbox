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

from math import ceil
from itertools import izip, count

from genlog import wrap as mlog

def countdown(n):
    while True:
        yield n
        n -= 1

class awesomeint(long):
    """ Teach an old int new tricks. """
    def __init__(self, x, base=10):
        self.base = base
    
    def __getitem__(self, item):
        if isinstance(item, slice):
            return numslice(self, item.start, item.stop, self.base)
        else:
            return nth(self, item, 1, self.base)


def nth(x, n, digits=1, system=10):
    if n < 0:
        return int(x / (system ** (abs(n) - 1))) % system ** digits
    else:
        return int(
            x / (system ** int(mlog.log(system)(x) - n))
            ) % system ** digits


def numslice(x, start=None, stop=None, system=10):
    if start is None:
        start = 0
    if stop is None:
        stop = int(mlog.log(system)(x)) + 1
        
    if start < 0 and stop >= 0:
        start = int(mlog.log(system)(x)) + 1 + start
    elif stop < 0 and start >= 0:
        stop = int(mlog.log(system)(x)) + 1 + stop
    
    if stop < start:
        raise ValueError
    
    return nth(x, max(start, stop - 1), abs(start - stop), system)
