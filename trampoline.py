# Copyright (c) 2011, Florian Mayer <flormayer@aim.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

def tail(fun, *args, **kwargs):
    if isinstance(fun, Trampoline):
        fun = fun.fun
    raise TailCall(fun, args, kwargs)


class TailCall(BaseException):
    pass


class Trampoline(object):
    def __init__(self, fun):
        self.fun = fun
    
    def __call__(self, *args, **kwargs):
        fun = self.fun
        while True:
            try:
                val = fun(*args, **kwargs)
            except TailCall, e:
                fun, args, kwargs = e.args
            else:
                break
        return val


if __name__ == '__main__':
    def baz():
        return 42
    
    @Trampoline
    def bar():
        tail(baz)
    
    @Trampoline
    def foo():
        tail(bar)
    
    print foo()

