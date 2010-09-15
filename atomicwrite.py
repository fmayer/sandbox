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

"""
Try to guarantee atomic write operations. On POSIX systems there should not
be a case where the file-system ends up being corrupted. On Windows the best
available method is chosen depending on the Windows Version, the only one that
is guaranteed to be atomic is on Windows Vista/Windows Server 2008 or better.
"""

import os
import sys
import shutil
import tempfile

CreateTransaction = None
MoveFileEx = None

if sys.platform == "win32":
    try:
        import ctypes
    except ImportError:
        pass
    else:
        try:
            ktmw32 = ctypes.windll.ktmw32
            CreateTransaction = ktmw32.CreateTransaction
            CommitTransaction = ktmw32.CommitTransaction
            kernel32 = ctypes.windll.kernel32
            MoveFileTransacted = kernel32.MoveFileTransactedW
            MOVEFILE_REPLACE_EXISTING = 1
        except (WindowsError, AttributeError):
            CreateTransaction = None
            try:
                MoveFileEx = kernel32.MoveFileExW
            except (WindowsError, AttributeError):
                pass


def win_atomic_mv(src, dst):
    """ Try to move src to dst as atomically as possible, overriding dst
    if it exists. """
    src = unicode(src)
    dst = unicode(dst)
    if CreateTransaction is None:
        if MoveFileEx is not None:
            # Fall back to MoveFileEx which is not guaranteed to be
            # atomic.
            MoveFileEx(src, dst, MOVEFILE_REPLACE_EXISTING)
        else:
            # Fall back to naive method.
            if os.path.exists(dst):
                tmp = tempfile.mktemp(dir=os.path.dirname(dst))
                os.rename(dst, tmp)
                try:
                    os.rename(src, dst)
                except (SystemExit, KeyboardInterrupt):
                    # A heroic attempt to save this sinking ship
                    # from filesystem corruption. We should not
                    # leave the file-system in an inconsistent state
                    # just because the program is shutting down.
                    os.rename(src, dst)
                finally:
                    os.unlink(tmp)
            else:
                os.rename(src, dst)
    else:
        # Use the transaction API which is guaranteed to be atomic. This
        # is avaiable from Windows Server 2008/Windows Vista onwards.
        trnid = CreateTransaction(None, 0, 0, 0, 0, None, "")
        MoveFileTransacted(
            src, dst, None, None, MOVEFILE_REPLACE_EXISTING, trnid
        )
        CommitTransaction(trnid)


def posix_atomic_mv(src, dst):
    """ Atomically move src to dst, overriding dst if it exists. """
    os.rename(src, dst)


if sys.platform == 'win32':
    atomic_mv = win_atomic_mv
elif os.name == 'posix':
    atomic_mv = posix_atomic_mv
else:
    raise EnvironmentError

class AtomicWrite(object):
    """
    Context manager to be used for atomic write operations. Returns a temporary
    file which is moved to the designated position as atomically as possible
    once the with-block ends without any exception. When an exception is
    raised in the with-block, the write is not done at all and the old file
    (if the write was supposed to be an override) is not touched. Append-mode
    is supported.
    
    >>> with AtomicWrite(os.path.join(os.environ['HOME'], 'testfoo'), 'ab') as fd:
    ...     fd.write('Foobar')
    ... 
    >>> 
    """
    def __init__(self, name, mode='wb'):
        # tempfile takes care of the correct umask by specifying
        # the mode attribute.
        tempfd, self.tempname = tempfile.mkstemp(
            dir=os.path.dirname(name)
        )
        self.temp = os.fdopen(tempfd, mode)
        self.name = name
        
        # Mock append mode.
        if 'a' in mode:
            shutil.copy(self.name, self.tempname)
    
    def __enter__(self):
        return self.temp
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            self.temp.flush()
            
            # We can safely use os.rename here because we told
            # mkstemp to create the temporary file in the same
            # directory the file to be replaced lies in, and thus
            # on the same file-system.
            try:
                self.temp.close()
                atomic_mv(self.tempname, self.name)
            except:
                if os.path.exists(self.tempname):
                    os.unlink(self.tempname)
                # We are not swallowing any errors here.
                raise


__all__ = ['AtomicWrite', 'atomic_mv', 'posix_atomic_mv', 'win_atomic_mv']


if __name__ == '__main__':
    with AtomicWrite(os.path.join(os.environ['HOME'], 'testfoo.txt'), 'wb') as fd:
        fd.write('Hallo Welt\n')
