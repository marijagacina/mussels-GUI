#!/usr/bin/env python

import json
import numpy
from socket import *
import time




def publish_json():
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.connect(('localhost', 4545))
    j = json.dumps({'mussels': [{'ID' : '1',
                                 'lat' : 45.789947 + 0.01 * numpy.sin(time.time()),
                                 'lng' : 16.989109 + 0.01 * numpy.cos(time.time()),
                                 'battery' : 3.3,
                                 'charging' : False
                                 },

                                {'ID': '22',
                                 'lat': 43.789947 + 0.01 * numpy.sin(time.time()),
                                 'lng': 15.989109 + 0.01 * numpy.cos(time.time()),
                                 'battery': 3.3,
                                 'charging': False
                                 },
                                    ]})
    sock.sendall(j.encode('utf-8'))


if __name__ == '__main__':
    publish_json()


