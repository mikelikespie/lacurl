# Copyright (c) 2009, Michael Lewis
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
from __future__ import with_statement

import cStringIO
import os
import threading


class LazyStream(object):
    __slots__ = ( 'consumers', 'producers', 'make_consumer', 'make_producer',
                    'producers_closed', '__init__', '_csio', '_cond', '_closing', 'consumers_closed')

    class LazyStreamConsumer(object):
        __slots__ = ('__init__', 'read', '_cond', '_csio', '_producers_closed_func', 'close',
                    '_closed', '_closing_func', 'closed')

        def __init__(self, csio, cond, producers_closed_func, closing_func):
            with cond:
                self._cond = cond
                self._csio = csio
                self._producers_closed_func = producers_closed_func
                self._closing_func = closing_func

        def read(self, leng=-1):
            with self._cond:
                if leng < 0:
                    #in this case, we want to block until all the producers
                    # are closed
                    while True:
                        if self._producers_closed_func():
                            return self._csio.read(leng)
                        else:
                            self._cond.wait()
                else:
                    # In this caes, we want to block until we can read leng bytes
                    # or the producers are closed
                    pos = self._csio.tell()
                    while True:
                        self._csio.seek(pos)
                        read = self._csio.read(leng)
                        if len(read) >= leng or self._producers_closed_func():
                            return read
                        else:
                            self._cond.wait()
        def readline(self):
            with self._cond:
                pos = self._csio.tell()
                while True:
                    self._csio.seek(pos)
                    read = self._csio.readline()
                    if (len(read) and read[-1] == '\n')  or \
                            self._producers_closed_func():
                        return read
                    else:
                        self._cond.wait()

        def readlines(self):
            return [l for l in self]

        def next(self):
            line = self.readline()
            if not line:
                raise StopIteration
            return line


        def close(self):
            with self._cond:
                self._closed = True
                self._closing_func()

        def _getclosed(self):
            with self._cond:
                return self._closed

        closed = property(_getclosed)

        def __str__(self):
            with self._cond:
                pos = self._csio.tell()
                r = self.read()
                self._csio.seek(pos)
                return r

        def __iter__(self):
            return self



    class LazyStreamProducer(object):
        __slots__ = ('__init__', 'write', 'close', 'closed', '_getclosed', '_cond', '_csio', '_closed')

        def __init__(self, csio, cond):
            with cond:
                self._cond = cond
                self._csio = csio
                self._closed = False

        def write(self, *s, **d):
            with self._cond:
                #if it's closed already, let's no-op
                if not self._csio.closed:
                    pos = self._csio.tell()
                    self._csio.seek(0, os.SEEK_END)
                    self._csio.write(*s, **d)
                    self._csio.seek(pos)
                    self._cond.notify()


        def close(self):
            with self._cond:
                self._closed = True
                self._cond.notify()

        def _getclosed(self):
            with self._cond:
                return self._closed

        closed = property(_getclosed)


    def __init__(self, *s, **d):
        self._csio = cStringIO.StringIO(*s, **d)
        self._cond = threading.Condition()
        self.consumers = []
        self.producers = []

    def _closing(self):
        with self._cond:
            if self.consumers_closed():
                self._csio.close()


    def consumers_closed(self):
        """
        Are all the consumers closed?
        """
        with self._cond:
            return all(c.closed for c in self.consumers)

    def producers_closed(self):
        """
        Are all the producers closed?
        """
        with self._cond:
            return all(c.closed for c in self.producers)

    def make_producer(self):
        with self._cond:
            prod = LazyStream.LazyStreamProducer(self._csio, self._cond)
            self.producers.append(prod)
            return prod

    def make_consumer(self):
        with self._cond:
            cons = LazyStream.LazyStreamConsumer(self._csio, self._cond, self.producers_closed, self._closing)
            self.consumers.append(cons)
            return cons











