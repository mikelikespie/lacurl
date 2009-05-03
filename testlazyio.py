from lazystream import LazyStream
import json
import threading
import time


def run(producer):
    print "sleeping for 3 seconds"
    print "producing"
    for i in range(10):
        time.sleep(.5)
        producer.write('line %s\n' % i)
    print "sleeping then closing"
    producer.close()
    print "closed"




ls = LazyStream()
p = ls.make_producer()
c = ls.make_consumer()


t = threading.Thread(target=run, args=(p,))
t.start()

for l in c:
    print "got a line: %s" % l.__repr__()

t.join()


