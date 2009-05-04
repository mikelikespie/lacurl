"""
Run this and pass a username as the first arg, and it will return time timeline for their first 50 friends.

This will make a lot of output, so please pipe it to a file
"""
from __future__ import with_statement

import sys

import lacurl.pool
import lacurl.ext.ajason

import urllib2
try:
    import simplejson as json
except ImportError:
    import json

import time


class timer(object):
    def __init__(self, name, stream = sys.stdout):
        self.name = name
        self.start = None
        self.stream = stream

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.time()

        print >>self.stream, "%s took %s seconds" % (self.name, end - self.start)


def main():
    if len(sys.argv) < 2:
        print >>sys.stderr, "usage: mini_bench.py <screen_name>"
        exit(1)
    user = sys.argv[1]



    def getlist(opener, loader, user):
        return (loader(opener('http://twitter.com/friends/ids/%s.json' % user)),
                loader(opener('http://twitter.com/followers/ids/%s.json' % user)))

    friends, followers = getlist(urllib2.urlopen, json.load, user)
    to_get = set(friends[:10] + followers[:10])

    print "getting %s urls" % len(to_get)

    with timer("using LAcURL asynchronously"):
        p = lacurl.pool.Pool(100)
        with p:
            l = [getlist(p.urlopen, lacurl.ext.ajason.load, u) for u in to_get]

            #let's copy them to new lists
            total_fetched = sum(len(a) + len(b) for a,b in l)
            print "%d fetched" % total_fetched

    with timer("using urllib2.urlopen serially"):
        l = [getlist(urllib2.urlopen, json.load, u) for u in to_get]

        #let's copy them to new lists
        total_fetched = sum(len(a) + len(b) for a,b in l)
        print "%d fetched" % total_fetched


if __name__ == "__main__":
    main()
