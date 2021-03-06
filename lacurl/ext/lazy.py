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

def lazy(*_possible_classes):
    """
    This function generates a lazy evaluator class

    pass it a list of possible return values for the callback
    """

    functions = set()
    properties = set()
    
    #Get the all the callable items
    for c in _possible_classes:
        functions.update(set([k for k,v in c.__dict__.iteritems() if  callable(v)]))
    #Get all the non-callable items
    for c in _possible_classes:
        properties.update(set([k for k,v in c.__dict__.iteritems() if not callable(v)]))

    if '__new__' in functions:
        functions.remove('__new__')

    functions.add('__callback')
    properties.add('__val')

    class lazy(object):
        class InvalidValue: pass #We need this so we can support none even

        __meta__ = tuple(_possible_classes)
        __slots__ = tuple(functions.union(properties))

        def __init__(self, callback):
            self.__callback = callback
            self.__val = lazy.InvalidValue

        def __getattribute__(self, attr):
            if attr in ('__getattribute__', '__slots__', '_lazy__callback') or \
                    (attr not in ('_lazy__val', '__class__', '__dict__', '__base__', '__bases__', #This is really dirty.
                        '__new__')
                            and attr not in self.__slots__):
                return object.__getattribute__(self, attr)

            if attr == '_lazy__val':
                if object.__getattribute__(self, attr) is lazy.InvalidValue:
                    object.__setattr__(self, attr, self.__callback())
                return object.__getattribute__(self, attr) 
            

            return self.__val.__getattribute__(attr)

    def makehook(f):
        return lambda self, *s, **d: self._lazy__val.__getattribute__(f)(*s, **d)

    for f in functions - set(('__callback', '__init__','__getattribute__')):
       setattr(lazy, f, makehook(f))

    
    return lazy


def test():
    def getlist():
        print "Getting List"
        return [1,2,3,4,5]

    def getdict():
        print "Getting dict"
        return {1:2,3:4}

    def getint():
        print "Getting int"
        return 52

    def getstr():
        print "Getting str"
        return "HELLO"

    def getfloat():
        print "Getting float"
        return 52.2

    def gettrue():
        print "getting false"
        return True

    def getfalse():
        print "getting false"
        return False

    def getnone():
        print "getting None"
        return None

    print "Making lazies"
    Lazy = lazy(list, dict, str, float, int, type(None), bool)
    lazies = [
     Lazy(getlist),
     Lazy(getstr),
     Lazy(getdict),
     Lazy(getint),
     Lazy(getnone),
     Lazy(gettrue),
     Lazy(getfalse),
     Lazy(getfloat)]
    print "Lazies made"

    for l in lazies:
        print l

    d = Lazy(getdict)

    print d.__repr__()
    print d
    repr = d.__repr__
    print repr()

    print type(d)
    print d.__class__

    print "d isinstanc of dict = %s" % isinstance(d, dict)


