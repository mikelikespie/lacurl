try:
    import simplejson as json
except ImportError:
    import json

import pylazy

Lazy = pylazy.makelazy(dict, list, unicode, int, long, float, bool)
def load(*s, **d):
    return Lazy(lambda: json.load(*s, **d))

