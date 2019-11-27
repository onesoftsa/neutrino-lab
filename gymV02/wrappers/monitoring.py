#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Implement an agent wrapper to include new methods to the original agent. Use
this implementation as a code base to write your render() function. It will
dump information to a client socket, generating a minimal impact on the
simulation time. Then, another process can access this socket to retrieve
data and build something upon that.


@author: ucaiado

Created on 09/05/2017
"""
import copy
import traceback
import neutrinogym.neutrino as neutrino
from neutrinogym.neutrino import fx, Source
import gc
import pickle
import json
import pandas as pd
import time
import socket

from neutrinogym.qcore import AgentWrapper

'''
Begin help functions
'''


def get_order_book(book, func):
    '''
    Return a dataframe representing the order book passed

    :param book. neutrino Book. Limit order book of a specific instrument
    :param func. neutrino function. Function byprice from API
    '''
    i_depth = 5
    l_col = ['qBid', 'Bid', 'Ask', 'qAsk']
    l_rtn = [[0, 0., 0., 0] for x in range(i_depth)]
    bid = func(book.bid(), i_depth)
    ask = func(book.ask(), i_depth)
    for x in xrange(i_depth):
        if bid and abs(bid[x].price) > 10e-4 and abs(bid[x].price) < 10**8:
            l_rtn[x][0] = '{:0.0f}'.format(bid[x].quantity)
            l_rtn[x][1] = '{:0.2f}'.format(bid[x].price)
        if ask and abs(ask[x].price) > 10e-4 and abs(ask[x].price) < 10**8:
            l_rtn[x][2] = '{:0.2f}'.format(ask[x].price)
            l_rtn[x][3] = '{:0.0f}'.format(ask[x].quantity)
    return l_rtn

ADDR = ('127.0.0.1', 12000)

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.settimeout(1)

'''
End help functions
'''


class Monitor(AgentWrapper):
    '''
    Monitor is used to including new methods to the agent that are not used
    in production environment and render information to be used in an external
    data visualization
    '''

    def __init__(self, agent):
        '''
        Initiate a Tester instance. Save all parameters as attributes

        :param agent: Agent object.
        '''
        super(Monitor, self).__init__(agent)
        self._baseagent += '_Monitor'
        # control img rendering
        self.update_delay = .5
        self.last_time = time.time() + 5
        # variable to keep the history of the simulation
        self.history = {}

    def flush(self, env):
        '''
        Flush all relevant monitor information

        :param env: Environment Object.
        '''
        self.render()
        # keep the history of the last position
        s_time = env.get_current_time()
        s_date = s_time.split(' ')[0]
        d_position = {}
        for s_symbol, instr in iter(self._instr_stack.items()):
            d_position[s_symbol] = copy.deepcopy(instr._position)
        self.history[s_date] = d_position

    def render(self):
        '''
        Render the books used by the agent
        '''
        if (time.time() - self.last_time) > self.update_delay:
            self.last_time = time.time()
            s_serialized = self.get_data_to_render()
            b = bytearray()
            b.extend(map(ord, s_serialized))
            clientSocket.sendto(b, ADDR)

    def get_data_to_render(self):
        '''
        Return a string with a JSON containing the data to be used by an
        external visualization
        '''
        d_to_pickle = {}
        # recover books
        for s_cmm in self._instr_from_conf:
            df_book = get_order_book(fx.book(s_cmm), neutrino.byPrice)
            d_to_pickle[s_cmm] = df_book
        # recover agent prices
        d_agent_prices = {}
        try:
            for instr in self._instr_stack:
                l_aux = [x for x in instr._prices['ASK'].keys()]
                l_aux += [x for x in instr._prices['BID'].keys()]
                d_agent_prices[instr.symbol_name] = l_aux
        except (KeyError, AttributeError) as e:
            pass
        d_to_pickle['agent_prices'] = d_agent_prices
        d_to_pickle['instruments'] = self._instr_from_conf
        d_to_pickle['time'] = fx.now(True)
        # s_serialized = pickle.dumps(d_to_pickle)
        s_serialized = json.dumps(d_to_pickle)
        # print d_to_pickle['DI1F23']
        # print 'string pickle size ', len(s_serialized)
        # print 'string json size ', len(json.dumps(d_to_pickle))
        return s_serialized
