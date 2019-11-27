#!/usr/bin/python
# -*- coding: future_fstrings -*-
"""
Implement a strategy to test the new API in production Environment


@author: ucaiado

Created on 10/29/2019
"""
from __future__ import print_function
import sys
import time
import neutrinogym.neutrino as neutrino

'''
Begin help functions
'''

PRINT_EVERY = 5

def epoch2str(epoch):
    # from Fredy
    mlsec = "000"
    if str(epoch).find(".") >= 0:
            mlsec = repr(epoch).split('.')[1][:3]
    return time.strftime(
        '[%Y-%m-%d %H:%M:%S.{}]'.format(mlsec), time.localtime(epoch))


def updateR2str(update_obj):
    s_rtn = ','.join(str(r) for r in update_obj.reason)
    return s_rtn

def updateT2str(update_obj):
    s_rtn = ','.join(str(r) for r in update_obj.times)
    return s_rtn


def trade2str(agent, i_id):
    ii = i_id
    try:
        trade_data = agent.instr[agent.my_symbol].trades[ii]
    except IndexError:
        import pdb; pdb.set_trace()
    return(
        f'trade_id={trade_data.trade_id}, '
        f'datetime={trade_data.datetime}, '
        f'price={trade_data.price}, '
        f'quantity={trade_data.quantity}, '
        f'buyer={trade_data.buyer}, '
        f'seller={trade_data.seller}, '
        f'status={trade_data.status}')

def book2str(agent, i_seq, s_times):
    bid = neutrino.byPrice(agent.instr[agent.my_symbol].book.bid, 5)
    ask = neutrino.byPrice(agent.instr[agent.my_symbol].book.ask, 5)
    s_book_msg = (
        'on_data: book_seq=%i, qbid=%.0f, bid=%.2f, ' +
        'ask=%.2f, qask=%.0f, times=%s')
    return(s_book_msg % (
        i_seq, bid[0].quantity, bid[0].price, ask[0].price, ask[0].quantity,
        s_times))

'''
End help functions
'''

class PrintTrades(object):
    def __init__(self):
        # initialize some variables
        self.i_count = 0
        self.i_count2 = 0
        self.last_seq = 0
        self.i_first_id = 0
        self._already_printed = False

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
                book_callback=None,
                trade_buffer_size=128)

    def on_data(self, update):
        # check if all structures is ready to be used
        this_instr = self.instr[self.my_symbol]
        if (not this_instr.ready()) or (self.my_symbol != update.symbol):
            return

        # print every PRINT_EVERY counts
        self.i_count += 1
        if self.i_count % PRINT_EVERY > 0:
            print('.', end="")  # , flush=True)
            return

        # NOTE: can comment that
        if self._already_printed:
            if self.i_count % (PRINT_EVERY * 3):
                self._already_printed = False
            return

        # print candle
        this_seq = this_instr.book.sequence
        s_reasons = updateR2str(update)
        s_updatetimes = updateT2str(update)
        s_time = epoch2str(neutrino.utils.now())
        # s_candle_msg = trade2str(self)
        s_book_msg = book2str(self, this_seq, s_updatetimes)
        print('\n\n' + s_time + s_book_msg)
        # print(s_time + s_candle_msg + '\n')
        self.instr[self.my_symbol]
        i_total = len(self.instr[self.my_symbol].trades)
        import pdb; pdb.set_trace()
        for ii in range(max(0, i_total - update.trade_count), i_total, 1):
            s_trade_msg = trade2str(self, i_id=ii)
            print('    ' + s_trade_msg + '\n')
        self.i_first_id = ii
        self._already_printed = True  # NOTE: can comment that
        sys.stdout.flush()

    def finalize(self, reason):
        self.i_count2 += 1
        s_t = epoch2str(neutrino.utils.now())
        print(f'{s_t}finalize {self.i_count, self.i_count2}: {str(reason)}')
        # neutrino.utils.quit()
