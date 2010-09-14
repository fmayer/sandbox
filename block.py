# Copyright (c) 2010 Florian Mayer

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

import threading


class LockedResource(object):
    """ Combine data with lock. Use with statement to acquire
    the data and lock it at the same time.
    
        >>> foo = LockedResource('foo')
        >>> with foo as bar:
        ...     print bar
        >>>
    """
    def __init__(self, data, lock=None):
        self.data = data
        if lock is None:
            lock = threading.Lock()
        self.lock = lock
    
    def __enter__(self):
        self.lock.acquire()
        return self.data
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.lock.release()


if __name__ == '__main__':
    foo = LockedResource('foo')
    with foo as bar:
        print bar
