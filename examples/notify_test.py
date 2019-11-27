#!/usr/bin/python
# -*- coding: future_fstrings -*-
"""
...


@author: ucaiado

Created on 11/21/2019
"""
from __future__ import print_function
import sys
import time
import json
import neutrinogym.neutrino as neutrino


'''
Begin help functions
'''


PRINT_EVERY = 50


def epoch2str(epoch):
    # from Fredy
    mlsec = "000"
    if str(epoch).find(".") >= 0:
            mlsec = repr(epoch).split('.')[1][:3]
    return time.strftime(
        '[%Y-%m-%d %H:%M:%S.{}]'.format(mlsec), time.localtime(epoch))


def book2str(agent, i_seq):
    bid = neutrino.utils.by_price(agent.instr[agent.my_symbol].book.bid, 5)
    ask = neutrino.utils.by_price(agent.instr[agent.my_symbol].book.ask, 5)
    s_book_msg = (
        '\n%son_data: book_seq=%i, qbid=%.0f, bid=%.2f, ' +
        'ask=%.2f, qask=%.0f')
    return(s_book_msg % (epoch2str(neutrino.utils.now()),i_seq, bid[0].quantity,
        bid[0].price, ask[0].price, ask[0].quantity))



'''
End help functions
'''


class NotifyTest(object):
    def __init__(self):
        # initialize some variables
        self.i_count = 0
        self.i_count2 = 0
        self.i_keep_going = 1
        self._config = {}
        self.all_orders = {'BID': {}, 'ASK': {}}
        self._time_to_quit = False
        if sys.version_info.major == 2:
            self.require_input = raw_input
        elif sys.version_info.major == 3:
            self.require_input = input

    # new callbacks
    def initialize(self, symbols):
        # initialize new variables
        self.symbols = []
        self.symbols2 = [s for s in symbols]
        self.symbols3 = symbols
        self.my_bar = None
        self.my_sma = None
        self.already_removed = False
        self.my_symbol = symbols[0]
        self.last_ts = 0
        self.instr = {}

        # add instruments
        for s_symbol in symbols:
            self.symbols.append(s_symbol)
            self.instr[s_symbol] = neutrino.market.add(
                symbol=s_symbol,
                trade_buffer_size=64)
            this_position = neutrino.position.get(s_symbol)
            if this_position.initial.net != 0:
                s_sinal = ''
                if this_position.initial.net > 0:
                    s_sinal = '+'
                print(f'!! {s_symbol} has an initial position of '
                      f'{s_sinal}{this_position.initial.net} '
                      f'@{this_position.initial.net_price}...\n')

        print('\n\n    symbols added: ', self.symbols2, '\n\n')  # , flush=True)

    def on_data(self, update):

        # check if all structures is ready to be used
        this_instr = self.instr[self.my_symbol]
        if not (this_instr.ready()) or (self.my_symbol != update.symbol):
            return

        # print every PRINT_EVERY counts
        self.i_count += 1
        if self.i_count % (PRINT_EVERY * self.i_keep_going) > 0:
            print('.', end="")  # , flush=True)
            return
        self.i_keep_going = 1

        if self._time_to_quit and self.i_count > 50:
            print('\n...quitting!!')  # , flush=True)
            neutrino.utils.quit()
            return
        elif not self._time_to_quit and self._config and self.i_count > 100:
            print(book2str(self, this_instr.book.sequence))  # , flush=True)
            this_position = neutrino.position.get(update.symbol)
            this_side=neutrino.Side.BID
            this_price=this_instr.book.ask[0].price
            if this_position.initial.net > 0:
                this_side = neutrino.Side.ASK
                this_price=this_instr.book.bid[0].price
            i_id = neutrino.order_client.send_limit_order(
                symbol=update.symbol,
                side=this_side,
                time_in_force=neutrino.TimeInForce.DAY,
                price=this_price,
                quantity=1)
            neutrino.utils.notify(f'I AM ALIVE AND THE FIRST ORDERS IN THE BOOK'
                                  f' ARE {this_instr.book.bid[0].quantity} '
                                  f'@{this_instr.book.bid[0].price} | '
                                  f'@{this_instr.book.ask[0].price} '
                                  f'{this_instr.book.ask[0].quantity} !!!!')
            self.i_count = self.i_count - 10
            self._time_to_quit = True
            print(f'ORDER SENT WAS ID {i_id}...')  # , flush=True)

    def order_update(self, order):
        print('...order update')

    def order_filled(self, order, lastpx, lastqty):
        print('... order filled')

    def set_parameters(self, config):
        if 'online' in config:
            self._config = '{"TestNotify":{"online":true}}'
        print('[set_parameters]', config)  # , flush=True)

    def get_parameters(self):
        print('[get_parameters]', self._config)
        return self._config

    def finalize(self, reason):
        self.i_count2 += 1
        s_t = epoch2str(neutrino.utils.now())
        print(f'{s_t}finalize {self.i_count, self.i_count2}: {str(reason)}')  # , flush=True)
        # neutrino.fx.quit()
