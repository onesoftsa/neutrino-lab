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

PRINT_EVERY = 50

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


def candle2str(agent, i_id=None):
    ii = i_id
    if isinstance(i_id, type(None)):
        ii = agent.my_bar.last_id
    t = agent.my_bar.timestamps[ii]
    o = agent.my_bar.open[ii]
    h = agent.my_bar.high[ii]
    l = agent.my_bar.low[ii]
    c = agent.my_bar.close[ii]
    q = agent.my_bar.quantity[ii]
    n = agent.my_bar.num_trades[ii]
    v = agent.my_bar.volume[ii]
    qb = agent.my_bar.quantity_buy[ii]
    qv = agent.my_bar.quantity_sell[ii]
    qcum = agent.my_bar.quantity_accumulated[ii]
    qbcum = agent.my_bar.quantity_buy_accumulated[ii]
    qscum = agent.my_bar.quantity_sell_accumulated[ii]
    sma = agent.my_sma.values[ii]
    adx = agent.my_adx.values[ii]
    atr = agent.my_satr.values[ii]
    s_rtn = (
        f'on_data: candleid={ii}, t={t}, o={o}, h={h}, l={l},'
        f'c={c}, q={q}, n={n}, v={v}, qb={qb}, qv={qv}, qcum={qcum}, '
        f'qbcum={qbcum}, qscum={qscum}, sma={sma}, adx={adx}, atr={atr}')
    if hasattr(agent, 'my_atr'):
        mon = agent.my_mom.values[ii]
        stddev = agent.my_stddev.values[ii]
        saadx = agent.my_saadx.values[ii]
        trange = agent.my_trange.values[ii]
        minus_di = agent.my_minus_di.values[ii]
        plus_di = agent.my_plus_di.values[ii]
        atr = agent.my_atr.values[ii]
        ema = agent.my_ema.values[ii]
        bbands1 = agent.my_bbands.bands[0][ii]
        bbands2 = agent.my_bbands.bands[1][ii]
        bbands3 = agent.my_bbands.bands[2][ii]
        sabbands1 = agent.my_sabbands.bands[0][ii]
        sabbands2 = agent.my_sabbands.bands[1][ii]
        sabbands3 = agent.my_sabbands.bands[2][ii]
        s_rtn += (
            f' ,mon={mon:.2f}, stddev={stddev:.2f}, saadx={saadx:.2f}, '
            f'saadx={saadx:.2f}, trange={trange:.2f}, '
            f'minus_di={minus_di:.2f}, plus_di={plus_di:.2f}, '
            f'atr={atr:.2f}, ema={ema:.2f}, bbands1={bbands1:.2f}, '
            f'bbands2={bbands2:.2f}, bbands3={bbands3:.2f}, '
            f'sabbands1={sabbands1:.2f}, sabbands2={sabbands2:.2f}, '
            f'sabbands3={sabbands3:.2f}')
    return s_rtn

def book2str(agent, i_seq, s_times):
    bid = neutrino.utils.by_price(agent.instr[agent.my_symbol].book.bid, 5)
    ask = neutrino.utils.by_price(agent.instr[agent.my_symbol].book.ask, 5)
    s_book_msg = (
        'on_data: book_seq=%i, qbid=%.0f, bid=%.2f, ' +
        'ask=%.2f, qask=%.0f, times=%s')
    return(s_book_msg % (
        i_seq, bid[0].quantity, bid[0].price, ask[0].price, ask[0].quantity,
        s_times))

def add_some_data(agent):
    agent.my_bar = neutrino.market.add_bar(
        agent.symbols3[0],
        bar_count=20,
        interval=1)
    agent.my_sma = agent.my_bar.add_sma(
        10, neutrino.IndicatorSource.CLOSE)
    agent.my_adx = agent.my_bar.add_adx(10)
    agent.my_satr = agent.my_bar.add_satr(10)


def add_all_data(agent):
    agent.my_bar = neutrino.market.add_bar(
        agent.symbols3[0],
        bar_count=200,
        interval=1)
    agent.my_sma = agent.my_bar.add_sma(
        bar_count=10, source=neutrino.IndicatorSource.CLOSE)
    agent.my_adx = agent.my_bar.add_adx(10)
    agent.my_satr = agent.my_bar.add_satr(10)  # , 10)
    agent.my_mom = agent.my_bar.add_mom(10, neutrino.IndicatorSource.CLOSE)
    agent.my_samom = agent.my_bar.add_samom(
        10, 5, neutrino.IndicatorSource.CLOSE)
    agent.my_stddev = agent.my_bar.add_stddev(
        10, 10, neutrino.IndicatorSource.CLOSE)
    agent.my_saadx = agent.my_bar.add_saadx(10, 10)
    agent.my_trange = agent.my_bar.add_trange()
    agent.my_minus_di = agent.my_bar.add_minus_di(10)
    agent.my_plus_di = agent.my_bar.add_plus_di(10)
    agent.my_atr = agent.my_bar.add_atr(10)
    agent.my_ema = agent.my_bar.add_ema(10, neutrino.IndicatorSource.CLOSE)
    agent.my_bbands = agent.my_bar.add_bbands(
        10, 2, 2, neutrino.IndicatorAverage.SMA)
    agent.my_sabbands = agent.my_bar.add_sabbands(
        10, 2, 2, 10, neutrino.IndicatorAverage.SMA)
    print(f'\n    Candle(symbol={agent.my_bar.properties.symbol}, '
          f'bar_count={agent.my_bar.properties.bar_count}, '
          f'interval={agent.my_bar.properties.interval}) subscribed\n')

'''
End help functions
'''

class PrintCandles(object):
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
                trade_buffer_size=64)

    def on_data(self, update):
        # add candles and indicators
        if isinstance(self.my_bar, type(None)):
            # add_some_data(self)
            add_all_data(self)

        # check if all structures is ready to be used
        this_instr = self.instr[self.my_symbol]
        if (not this_instr.ready()) or (self.my_symbol != update.symbol):
            return

        # print every PRINT_EVERY counts
        self.i_count += 1
        if self.i_count % PRINT_EVERY > 0:
            print('.', end="")  # , flush=True)
            return
        if (not self.my_bar) or (not self.my_bar.ready()):
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
        # s_candle_msg = candle2str(self)
        s_book_msg = book2str(self, this_seq, s_updatetimes)
        print('\n\n' + s_time + s_book_msg)
        # print(s_time + s_candle_msg + '\n')
        for ii in range(self.i_first_id, self.my_bar.last_id + 1):
            s_candle_msg = candle2str(self, i_id=ii)
            print('    ' + s_candle_msg + '\n')
        self.i_first_id = ii
        self._already_printed = True  # NOTE: can comment that
        sys.stdout.flush()

    def finalize(self, reason):
        self.i_count2 += 1
        s_t = epoch2str(neutrino.utils.now())
        print(f'{s_t}finalize {self.i_count, self.i_count2}: {str(reason)}')
        # neutrino.market.quit()
