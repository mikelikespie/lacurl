def makelazy(callback, *_possible_classes):
    functions = set()
    properties = set()
    
    #Get the all the callable items
    for c in _possible_classes:
        functions.update(set([k for k,v in c.__dict__.iteritems() if  callable(v)]))
    #Get all the non-callable items
    for c in _possible_classes:
        properties.update(set([k for k,v in c.__dict__.iteritems() if not callable(v)]))

    functions.remove('__new__')

    functions.add('__callback')
    functions.add('_val')

    class inner_lazy(object):
        __meta__ = tuple(_possible_classes)
        __slots__ = tuple(functions.union(properties))

        def __init__(self, callback):
            self.__callback = callback
            self._val = None

        def __getattribute__(self, attr):
            if attr in ('__getattribute__', '__slots__', '_inner_lazy__callback') or attr not in self.__slots__:
                return object.__getattribute__(self, attr)

            if attr == '_val':
                if object.__getattribute__(self, attr) is None:
                    object.__setattr__(self, attr, self.__callback())
                return object.__getattribute__(self, attr) 
            

            return self._val.__getattribute__(attr)
                
    new_lazy = inner_lazy(callback)

    functions -= set(('__callback', '__init__', '_val', '__getattribute__'))
    
    def makehook(f):
        return lambda *s, **d: new_lazy._val.__getattribute__(f)(*s, **d)

    for f in functions:
        object.__setattr__(new_lazy, f, makehook(f))

    return new_lazy


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

    print "Making lazies"
    lazies = [
     makelazy(getlist, list, dict, str, float, int),
     makelazy(getstr, list, dict, str, float, int),
     makelazy(getdict, list, dict, str, float, int),
     makelazy(getint, list, dict, str, float, int),
     makelazy(getfloat, list, dict, str, float, int)]
    print "Lazies made"

    for l in lazies:
        print l

    d = makelazy(getdict, list, dict, str, float, int)

    print d.__repr__()
    print d

    repr = d.__repr__
    print repr()


