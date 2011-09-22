#!/usr/bin/python
##############################################################################
#
# File:    stresser.py              
#
# This file is a part of Shoddy Battle.
# Copyright (C) 2011  Catherine Fitzpatrick and Benjamin Gwin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, visit the Free Software Foundation, Inc.
# online at http://gnu.org.
#
##############################################################################

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
        p = Process(target=start_challenger, args=('localhost', 9000, 'challenger%i' % i, 'test'))
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
