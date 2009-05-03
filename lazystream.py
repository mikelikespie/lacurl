import StringIO # use this just ofr it's interface
import cStringIO
import os
import threading


class LazyStream(object):
    __slots__ = ( 'consumers', 'producers', 'make_consumer', 'make_producer',
                    'producers_closed', '__init__', '_csio', '_cond',)

    class LazyStreamConsumer(object):
        __slots__ = ('__init__', 'read', '_cond', '_csio', '_producers_closed_func')

        def __init__(self, csio, cond, producers_closed_func):
            with cond:
                self._cond = cond
                self._csio = csio
                self._producers_closed_func = producers_closed_func

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
            cons = LazyStream.LazyStreamConsumer(self._csio, self._cond, self.producers_closed)
            self.consumers.append(cons)
            return cons











