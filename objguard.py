# (C) 2009 by Florian Mayer

import threading

class ObjectLocker(object):
    """ Manage access to an object. """
    def __init__(self):
        self.exclusive_lock = threading.Lock()
        self.sharedcount_lock = threading.Lock()
        self.noshared = threading.Event()
        
        # No readers in the beginning.
        self.sharedcount = 0
        self.noshared.set()
    
    def acquire_shared(self):
        """ Acquire shared access for object. You must call release_shared
        after you have finished your access on the object. Be careful to
        not accidentally alter the object, as it cannot be enforced. """
        # If a object is locked exclusively, wait for it to finish here.
        self.exclusive_lock.acquire()
        self.exclusive_lock.release()
        
        self.sharedcount_lock.acquire()
        try:
            if self.noshared.isSet():
                self.noshared.clear()
            self.sharedcount += 1
        finally:
            self.sharedcount_lock.release()
    
    def release_shared(self):
        """ End shared access. This must be called once for every call of
        acquire_shared. """
        self.sharedcount_lock.acquire()
        try:
            self.sharedcount -= 1
            if self.sharedcount == 0:
                self.noshared.set()
        finally:
            self.sharedcount_lock.release()
    
    def acquire_exclusive(self):
        """ Lock the object for exclusive access. This waits for all shared
        locks to return control of the object. Every subsequent acquire will
        wait until exclusive access is returned. """
        # The lock is acquired before we wait for the shared to finish,
        # because this way it is impossible that the exclusive waits a very
        # long time due to many shared being spawned.
        self.exclusive_lock.acquire()
        self.noshared.wait()
    
    def release_exclusive(self):
        """ End exclusive access. This must be called once for every call of
        acquire_exclusive. """
        self.exclusive_lock.release()


# Example follows.
import time

# Lock for standard output.
outlock = threading.Lock()

class Writer(threading.Thread):
    def __init__(self, locker, block, name):
        threading.Thread.__init__(self)
        
        self.locker = locker
        self.block = block
        self.name = name
    
    def run(self):
        self.locker.acquire_exclusive()
        outlock.acquire()
        try:
            print "Writer %s started." % self.name
        finally:
            outlock.release()
        try:
            time.sleep(self.block)
        finally:
            self.locker.release_exclusive()
        outlock.acquire()
        try:
            print "Writer %s finished." % self.name
        finally:
            outlock.release()


class Reader(threading.Thread):
    def __init__(self, locker, block, name):
        threading.Thread.__init__(self)
        
        self.locker = locker
        self.block = block
        self.name = name
    
    def run(self):
        self.locker.acquire_shared()
        outlock.acquire()
        try:
            print "Reader %s started." % self.name
        finally:
            outlock.release()
        try:
            time.sleep(self.block)
        finally:
            self.locker.release_shared()
        outlock.acquire()
        try:
            print "Reader %s finished." % self.name
        finally:
            outlock.release()


def main():
    locker = ObjectLocker()
    Reader(locker, 5, '1').start()
    Reader(locker, 5, '2').start()
    Reader(locker, 3, '3').start()
    Writer(locker, 3, '4').start()
    Reader(locker, 0, '5').start()


if __name__ == '__main__':
    main()
