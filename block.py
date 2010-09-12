# (C) 2010 by Florian Mayer

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
