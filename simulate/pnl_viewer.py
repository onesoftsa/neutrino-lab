#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Visualize the orders of an agent in a LOB. Use this implementation as a starter
code to implement the visualizations you need. It requires that you use a
wrapper as the Monitor wrappers implemented in `wrappers` folder.


@author: ucaiado

Created on 01/11/2018
"""

import time
import socket
import pickle
import json
import numpy as np
import pandas as pd
from datetime import datetime

'''
Begin help functions
'''


'''
End help functions
'''


if __name__ == '__main__':
    # initiate socket connection
    addr = ('127.0.0.1', 12000)

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(('', 12000))

    # initiate the animation
    message, address = serverSocket.recvfrom(1024)

    # d_data = pickle.loads(message)
    d_data = json.loads(message)

    # set the list of instruments used in conf file
    INSTRUMENTS = d_data['instruments']

    t_figsize = (8, 4)
    if len(INSTRUMENTS) > 3:
        t_figsize = (11, 8)

    while True:
        message, address = serverSocket.recvfrom(1024)
        d_data = json.loads(message)

        d_count = {k: len(d_data['agent_prices'][k])
        for k in d_data['agent_prices'].keys()
        }

        print('[%s] %s, %s, %s' % (
            d_data['time'][:-3],
            'PnL: R$ {:.01f}'.format(d_data['pnl']),
            'Pos: {:.0f}'.format(d_data['position']),
            'Num. agent prices: {:s}'.format(d_count))
        )

    # Uncomment the next line if you want to save the animation
    # simulation.save(filename='sim.html',fps=30,dpi=300)

    plt.show()
