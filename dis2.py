# (C) 2009 by Florian Mayer

import dis

def lookup(co, op, oparg):
    if op in dis.hasconst:
        return co.co_consts[oparg]
    elif op in dis.hasname:
        return co.co_names[oparg]
    elif op in dis.hasjrel:
        return repr(i + oparg)
    elif op in dis.haslocal:
        return co.co_varnames[oparg]
    elif op in dis.hascompare:
        return cmp_op[oparg]
    elif op in dis.hasfree:
        free = co.co_cellvars + co.co_freevars
        return free[oparg]

def disassemble(co, lasti=-1):
    """Disassemble a code object."""
    code = co.co_code
    labels = dis.findlabels(code)
    linestarts = dict(dis.findlinestarts(co))
    n = len(code)
    i = 0
    extended_arg = 0
    free = None
    while i < n:
        c = code[i]
        op = ord(c)
        i = i+1
        oparg = None
        if op >= dis.HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256 + extended_arg
            extended_arg = 0
            i = i+2
            if op == dis.EXTENDED_ARG:
                extended_arg = oparg*65536L
        yield (op, oparg)
