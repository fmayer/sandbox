# (C) 2009 by Florian Mayer

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
