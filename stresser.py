#!/usr/bin/python
from bot import *
from pyfred import *
from challenger import *
from parser import *
import time
from multiprocessing import Process
import sys

def stresser():
    pool = []
    p = Process(target=start_pyfred)
    p.start()
    pool.append(p)
    time.sleep(2)
    for i in range(0, 100):
        p = Process(target=start_challenger, args=('localhost', 8446, 'challenger%i' % i, 'test'))
        p.start()
        pool.append(p)
        time.sleep(0.01)
    return pool

def main(argv):
    while True:
        q = stresser()
        #time.sleep(30)
        for i in q:
            i.terminate()
        time.sleep(2)

if __name__ == '__main__':
    os.close(sys.stderr.fileno()) # hide pointless stack traces
    main(sys.argv)
