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

import dis2
import dis
import types

def find_imports(fun):
    imps = set()
    globs = set()
    mod = __import__(fun.__module__)
    lastop = -1
    glob = False
    jump_glob = False
    for op, oparg in dis2.disassemble(fun.func_code):
        if jump_glob:
            jump_glob = False
        # print op
        if op == dis.opmap['LOAD_GLOBAL']:
            modname = dis2.lookup(fun.func_code, op, oparg)
            lastmod = getattr(mod, modname)
            # print lastmod
            if isinstance(lastmod, types.ModuleType):
                imps.add(modname)
                glob = True
            else:
                globs.add(modname)
        elif jump_glob:
            pass
        elif op == dis.opmap['LOAD_ATTR']:
            # print glob
            if not glob:
                continue
            aname = dis2.lookup(fun.func_code, op, oparg)
            modname = modname + '.' + dis2.lookup(fun.func_code, op, oparg)
            try:
                lastmod = getattr(lastmod, aname)
            except AttributeError:
                # Stop resolving attributes until the next global name
                # is met.
                jump_glob = True
                continue
            # print lastmod
            if isinstance(lastmod, types.ModuleType):
                imps.add(modname)
        else:
            glob = False
        lastop = op
    return imps, globs


if __name__ == '__main__':
    import imps
    a = 1
    import asynchia
    import asynchia.maps
    
    def foo():
        a.__str__()
        asynchia.IOHandler
        asynchia.maps.PollSocketMap
        foo
    
    # print list(dis2.disassemble(foo.func_code))
    print imps.find_imports(foo)
    # print dis.dis(foo)
