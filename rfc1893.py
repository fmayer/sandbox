# Copyright (c) 2010 Florian Mayer <flormayer@aim.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
import email
import optparse

__version__ = '0.1.0'


def open_nonexisting(*args):
    if os.path.exists(args[0]):
        raise EnvironmentError
    else:
        return open(*args)


def mkor(fn, n):
    def _or(*args):
        if args[n] is None:
            return None
        return fn(*args)
    return _or


def is_permanent_failure(message, prnt=None, main=None):
    if main is None:
        main = message
    status = message.get("Status")
    if (
        status is not None and prnt is not None and
        prnt.get_content_type() == 'message/delivery-status'
        ):
        return (status.startswith("5"), message)
    if message.is_multipart():
        for child in message.get_payload():
            flr = is_permanent_failure(child, message, main)
            if flr[0]  is not None:
                return flr
    return None, None


if __name__ == "__main__":
    parser = optparse.OptionParser(
        prog="rfc1893",
        usage='rfc1893 [options] [input files]',
        version='rfc1893 ' + __version__
    )
    
    parser.add_option("-p", "--permanent", action="store", default=None,
                  type="str", dest="permanent", metavar="FILE",
                  help="Write addressees that are guaranteed to be "
                  "permanent failures to FILE."
                  "Pass - to write to standard output")
    
    parser.add_option("-t", "--temp", action="store", default=None,
                  type="str", dest="temp", metavar="FILE",
                  help="Write addressees that are guaranteed to be "
                  "temporary failures to FILE. "
                  "Pass - to write to standard output")
    
    parser.add_option("--fpermanent", action="store", default=None,
                  type="str", dest="fpermanent", metavar="FILE",
                  help="Write names of email files that are guaranteed to be "
                  "permanent failures to FILE."
                  "Pass - to write to standard output")
    
    parser.add_option("--ftemp", action="store", default=None,
                  type="str", dest="ftemp", metavar="FILE",
                  help="Write names of email files that are guaranteed to be "
                  "temporary failures to FILE."
                  "Pass - to write to standard output")
    
    parser.add_option("-u", "--funknown", action="store", default=None,
                  type="str", dest="funknown", metavar="FILE",
                  help="Write names of email files where delivery status " 
                  "is unknown to FILE."
                  "Pass - to write to standard output")
    
    parser.add_option('-f', '--force', action='store_true', dest='force',
                      default=False, help="Authorize program to override "
                      "existing files.")
    
    parser.add_option('-a', '--abspath', action='store_true', dest='abspath',
                      default=False, help="Output filenames as absolute "
                      "paths rather than relative ones.")
    
    options, args = parser.parse_args()
    
    if not args or all(
        x is None for x in [options.permanent, options.fpermanent,
                            options.temp, options.ftemp,
                            options.funknown]
        ):
        print parser.format_help()
        sys.exit(0)
    
    if options.force:
        op = open
    else:
        op = open_nonexisting
    
    _open_or = mkor(op, 0)
    
    statm = {
            True: [
                fl == '-' and sys.stdout or _open_or(fl, 'w') 
                for fl in [options.permanent, options.fpermanent]
                ],
            False: [
                fl == '-' and sys.stdout or _open_or(fl, 'w') 
                for fl in [options.temp, options.ftemp]
                ],
            None: [
                None,
                options.funknown == '-' and sys.stdout
                or _open_or(options.funknown, 'w')
                ],
    }
    
    try:        
        for fname in args:
            fd = open(fname)
            try:
                em = email.message_from_file(fd)
            
                status, message = is_permanent_failure(em)
                fcsv, acsv = statm[status]
                if fcsv is not None:
                    fcsv.write(
                        message.get('Final-Recipient').split("; ")[-1] + '\n'
                    )
                if acsv is not None:
                    if options.abspath:
                        acsv.write(os.path.abspath(fname) + '\n')
                    else:
                        acsv.write(fname + '\n')
            finally:
                fd.close()
    finally:
        for key, value in statm.iteritems():
            for fd in value:
                if fd is not None and fd is not sys.stdout:
                    fd.close()
