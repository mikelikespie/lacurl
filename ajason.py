try:
    import simplejson as json
except ImportError:
    import json

import pylazy

def load(*s, **d):
    return pylazy.makelazy(lambda: json.load(*s, **d), dict, list, unicode, int, long, float, True, False)

