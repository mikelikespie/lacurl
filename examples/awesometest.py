"""
Run this and pass a username as the first arg, and it will return time timeline for their first 50 friends.

This will make a lot of output, so please pipe it to a file
"""
from __future__ import with_statement

import sys

import lacurl
from lacurl.ext.ajason import load


user = sys.argv[1]


p = lacurl.Pool(50)

with p:
    f = p.urlopen('http://twitter.com/friends/ids/%s.json' % user)
    u = load(f)

    #let's get your first 50 friends' timelines
    first = u[:50]

    fs = [load(p.urlopen('http://twitter.com/statuses/user_timeline.json?user_id=%s' % id)) for id in first] 


    for status in fs:
        print fs

    print 'finishing'
