#! /usr/bin/env python

# Copyright (c) 2009, Daniel Robert Farina
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials
#       provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import pycurl
from cStringIO import StringIO
from collections import deque

class POST:
    pass

class GET:
    pass

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass

class URLFetch(object):
    def __init__(self, url, method=GET, payload=None):
        """
        Enough information to fetch a given URL using the Pool object

        method defaults to GET; if made POST

        """
        self.url = url
        self.method = method
        self.payload = payload

        # Prevent a careless 'None' payload
        if method not in [GET, POST]:
            errormsg = ' '.join(['only the GET and POST objects from module',
                                 '"{0}" may be specified as a method'])
            errormsg = errormsg.format(self.__module__)
            raise TypeError(errormsg)
        if method is POST and payload is None:
                TypeError('POST method specified without payload')


class Pool(object):
    def __init__(self, concurrency_level, poll_interval=1.0):
        """
        Initializes a multi-curl pool for requests

        The pool will be as large as the supplied concurrency_level.
        The poll_interval determines the timeout of the select() call

        """
        self.poll_interval = poll_interval
        self.m = m = pycurl.CurlMulti()
        m.handles = []
        # build the pool of curl objects
        for i in xrange(concurrency_level):
            c = pycurl.Curl()
            c.buf = None
            c.urlfetch = None
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.MAXREDIRS, 5)
            c.setopt(pycurl.CONNECTTIMEOUT, 30)
            c.setopt(pycurl.TIMEOUT, 300)
            c.setopt(pycurl.NOSIGNAL, 1)
            m.handles.append(c)

    def perform(self, *urls):
        """
        Given one or more URLFetch objects enqueue them all and serve
        them as quickly as possible.

        Returns a dictionary mapping the supplied URLFetch objects to
        their response bodies.

        """

        def clear_curlobj(c):
            # clear fields on c to make things easier to debug
            c.buf.close()
            c.buf = None
            c.urlfetch = None

        num_processed = 0
        freelist = self.m.handles[:]
        complete = {}

        queue = list(urls)
        while num_processed < len(urls):

            # This loop is run when there is work to be done and extra
            # capacity to do it with.  Pop a curl object and a
            # urlfetch object off their respective queues and set them
            # up to get to work.
            while queue and freelist:
                urlfetch = queue.pop()
                c = freelist.pop()

                c.setopt(pycurl.URL, urlfetch.url)
                buf = StringIO()

                c.setopt(pycurl.WRITEFUNCTION, buf.write)
                self.m.add_handle(c)

                if urlfetch.method is POST:
                    c.setopt(pycurl.POSTFIELDS, urlfetch.payload)
                elif urlfetch.method is GET:
                    c.setopt(pycurl.HTTPGET, 1)
                else:
                    raise TypeError('only the GET and POST objects from '
                                    'module {0} are allowed', self.__module__)

                c.urlfetch = urlfetch
                c.buf = buf

            # Run the internal curl state machine for the multi stack.
            while 1:
                ret, num_handles = self.m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            # Check for curl objects which have terminated, and add
            # them to the freelist after recording the results
            while 1:
                num_q, ok_list, err_list = self.m.info_read()
                for c in ok_list:
                    complete[c.urlfetch] = c.buf.getvalue()

                    clear_curlobj(c)
                    self.m.remove_handle(c)
                    freelist.append(c)

                for c, errno, errmsg in err_list:
                    e = IOError(errno, errmsg)
                    e.urlfetch = c.urlfetch
                    complete[c.urlfetch] = e

                    clear_curlobj(c)
                    self.m.remove_handle(c)
                    freelist.append(c)

                num_processed += len(ok_list) + len(err_list)
                if num_q == 0:
                    break
            # Currently no more I/O is pending, could do something in the meantime
            # (display a progress bar, etc.).
            # We just call select() to sleep until some more data is available.
            self.m.select(self.poll_interval)

        return complete

    def __del__(self):
        # Cleanup
        for c in self.m.handles:
            if c.buf is not None:
                c.buf.close()
                c.buf = None
            c.close()
        self.m.close()
