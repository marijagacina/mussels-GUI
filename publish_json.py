#!/usr/bin/env python

import json
from socket import *
import time
from random import randrange, choice
from numpy import random

mussel_pos = {}
stat_A = {}
stat_B = {}
vol_A = {}
vol_B = {}
curr_A = {}
curr_B = {}
press = {}
temp = {}

def init_mussels(n):
    for i in range(n):
        mussel_pos[i] = [randrange(-50,50), randrange(-50,50)]
        stat_A[i] = choice([0,1])
        stat_B[i] = choice([0,1])
        vol_A[i] = randrange(1,4)
        vol_B[i] = randrange(1,4)
        curr_A[i] = randrange(-100,400)
        curr_B[i] = randrange(-100,400)
        press[i] = randrange(950,1200)
        temp[i] = randrange(-30,40)

def publish_json(n):
    it = 0
    i = 0
    while True:
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect(('localhost', 4545))
        # prepare data to be published 
        pos_x = mussel_pos[i][0] + random.normal(0, 0.1, size=None)
        pos_y = mussel_pos[i][1] + random.normal(0, 0.1, size=None)
        stat_A_ = stat_A[i]
        stat_B_ = stat_B[i]
        vol_A_ = vol_A[i] - it * 0.0001
        vol_B_ =  vol_B[i] - it * 0.0001
        curr_A_ = curr_A[i] + random.normal(0, 1, size=None)
        curr_B_ = curr_B[i] + random.normal(0, 1, size=None)
        press_ = press[i] + random.normal(0, 1, size=None)
        temp_ = temp[i] + random.normal(0, 1, size=None)

        j = json.dumps({"id": i, "pos_x": pos_x, "pos_y": pos_y, "chrg_1": stat_A_, "chrg_2": stat_B_, "v_1": vol_A_, \
            "v_2": vol_B_, "c_1": curr_A_, "c_2": curr_B_, "press": press[i], "temp": temp[i]})
        sock.sendall(j.encode("utf-8"))

        print ("Sending", i, pos_x, pos_y, stat_A_, stat_B_, vol_A_, vol_B_, curr_A_, curr_B_, press_, temp_)
        time.sleep(0.2)
        i+=1
        i = i % n
        it+=1

if __name__ == '__main__':
    init_mussels(10)
    publish_json(10)


