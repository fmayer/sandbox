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
