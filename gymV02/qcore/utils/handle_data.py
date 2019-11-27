#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Implement the classes required to handle orders and the access to information
related to books and candles subscribed by an agent


@author: ucaiado

Created on 07/05/2018
'''
import os
import yaml
from collections import namedtuple
import numpy as np

from neutrinogym.qcore import PROD

if not PROD:
    from neutrinogym import neutrino
    from neutrinogym.neutrino import fx
else:
    import neutrino
    from neutrino import fx
from .neutrino_utils import (get_begin_time, SymbolSubscriptionError)
from .handle_orders import Instrument

import pdb;

'''
Begin help functions
'''

s_trade_info = 'price qty buyer seller time agr trade_id'
TradeInfo = namedtuple('TradeInfo', s_trade_info)
OrderLevelInfo = namedtuple('OrderLevelInfo', 'price qty order_id broker')
PriceLevelInfo = namedtuple('PriceLevelInfo', 'price qty')
s_order_info = 'neutrino_order symbol side order_id price qty '
s_order_info += 'cum_qty status secondary_order_id time_in_force id is_alive '
s_order_info += 'is_pending'
OrderInfo = namedtuple('OrderInfo', s_order_info)
s_count_info = 'bid_count ask_count trade_count new_bid cancel_bid '
s_count_info += 'replace_bid new_ask cancel_ask replace_ask status_changed'
CountsInfo = namedtuple('CountsInfo', s_count_info)


def fill_orderinfo(order):
    return OrderInfo(order, order.symbol, str(order.side), 'None',  # order.orderId,
                     order.current.price, order.current.qty,
                     order.current.cumQty, str(order.current.status),
                     order.current.secondaryOrderID,
                     str(order.current.timeInForce),
                     order.userData['id'], order.isAlive(), order.isPending())


'''
End help functions
'''


class CandlesHandler(object):
    '''
    Candles Data Handler
    '''
    def __init__(self):
        '''
        Instanciate a CandlesHandler object
        '''
        self._data_holder = {}
        self._alias = {}
        self._key_to_alias = {}
        self.b_should_load_again = False

    def reset(self, this_candle=None, this_conf=None):
        '''
        Unsubscribe all data
        '''
        b_t = not isinstance(this_conf, type(None))
        if isinstance(this_candle, type(None)):
            for this_candle in self._data_holder.values():
                for d_conf in this_candle.l_to_subscribe:
                    try:
                        fx.unsubscribeIndicator(str(d_conf['symbol']),
                                                str(d_conf['what']),
                                                str(d_conf['conf']),
                                                this_candle.i_lastbgtime)
                    except IndexError:
                        pass
                del this_candle
            self._data_holder = {}
            self._alias = {}
            self._key_to_alias = {}
        else:
            for d_conf in this_candle.l_to_subscribe:
                if str(d_conf['what']) != 'CANDLE' and b_t:
                    if sum(
                        [(d_conf[s_key]!=this_conf[s_key]) * 1
                        for s_key in this_conf]):
                        continue
                try:
                    fx.unsubscribeIndicator(str(d_conf['symbol']),
                                            str(d_conf['what']),
                                            str(d_conf['conf']),
                                            this_candle.i_lastbgtime)
                except IndexError:
                    pass
            if not b_t:
                self._data_holder.pop(this_candle.main_key)
                self._alias.pop(self._key_to_alias[this_candle.main_key])
                self._key_to_alias.pop(this_candle.main_key)
                del this_candle

    def check_pending_candles_subscriptions(self, fx_now):
        if self.b_should_load_again:
            self.b_should_load_again = False
            self.on_symbols_load(fx_now)

    def subscribe(self, s_symbol, interval, i_nbars, s_alias, s_type=None):
        '''
        Subscribe the data streaming of a new candle

        :param s_symbol: string. symbol to be subscribed
        :param interval: CandleIntervals object. The interval of the candle
        :param i_nbars: integer.
        :param s_alias: string. An alias to the candle
        :return: CandleData.
        '''
        self.b_should_load_again = True
        if not isinstance(interval, int):
            i_interval = interval.value
        else:
            i_interval = interval * 60
        s_key = '{}:interval={:0.0f}'.format(s_symbol, i_interval)
        self._alias[s_alias] = s_key
        self._key_to_alias[s_key] = s_alias
        if s_key not in self._data_holder:
            self._data_holder[s_key] = CandleData(s_symbol, i_interval,
                                                  i_nbars)
        self._data_holder[s_key].set_name(s_alias)
        return self._data_holder[s_key]

    def on_symbols_load(self, f_fxnow):
        '''
        Initiate the Candles attributes when the instrument is synchronized

        :param f_fxnow: float. the current time, in seconds
        '''
        self.b_should_load_again = False
        s_txt = None
        for this_candle in iter(self._data_holder.values()):
            if this_candle.v3_obj:
                this_candle.v3_obj.b_ready = True
            s_txt = this_candle.on_symbols_load(f_fxnow)
        return s_txt

    def add_indicator_to(self, this_candle, **kwargs):
        '''
        Add a new indicator to the candle passed

        :param s_ta_name: string. Indicator name (ta-lib)
        :param i_time_period: inter. rolling windows length
        :param s_input: string. the input used by SMA and EMA
        :param s_alias: string. alias to the indicator
        :return: CandleData object.
        '''
        self.b_should_load_again = True
        return this_candle.add_indicator(**kwargs)

    def get_candle(self, s_alias=None, s_symbol=None, i_interval=None):
        '''
        Return the candle data related to the the alias or symbol/interval

        :param s_symbol: string. symbol to be subscribed
        :param i_interval: integer. The interval of the candle, in seconds
        :return: CandleData object.
        '''
        if not s_symbol:
            s_key = self._alias.get(s_alias, None)
            # if not s_key:
            #     return None
            return self._data_holder.get(s_key, None)
        s_key = '{}:interval={:0.0f}'.format(s_symbol, i_interval)
        return self._data_holder.get(s_key, None)

    def get_current_value(self, this_candle, s_alias, i_iidx=0):
        '''
        Return the current value of the information required

        :param this_candle: CandleData object. Candle to retrive information
        :param s_alias: string. alias to the indicator desired
        :return: float. The value of the information required
        '''
        return this_candle.get_value(s_alias, -1, i_inner_idx=i_iidx)

    def get_previous_value(self, this_candle, s_alias, i_iidx=0):
        '''
        Return the previous value of the information required

        :param this_candle: CandleData object. Candle to retrive information
        :param s_alias: string. alias to the indicator desired
        :return: float. The value of the information required
        '''
        return this_candle.get_value(s_alias, -2, i_inner_idx=i_iidx)

    def get_value(self, this_candle, s_alias, i_idx, i_iidx=0):
        '''
        Return the value of the information required in the index passed

        :param this_candle: CandleData object. Candle to retrive information
        :param s_alias: string. alias to the indicator desired
        :param i_idx: integer. position of the information in array
        :return: float. The value of the information required
        '''
        return this_candle.get_value(s_alias, i_idx, i_inner_idx=i_iidx)

    def get_all_values(self, this_candle, s_alias):
        '''
        Return all values of the information required

        :param this_candle: CandleData object. Candle to retrive information
        :param s_alias: string. alias to the indicator desired
        :return: numpy array. The values of the information required
        '''
        l_basic = ['HIGH', 'LOW', 'CLOSE', 'OPEN', 'QTY', 'VOLUME', 'TS',
                   'QTY_BUYER', 'QTY_SELLER', 'CUMQTY_SELLER', 'CUMQTY_BUYER',
                   'CUMQTY']
        s_info2 = ''
        if s_alias not in l_basic:
            s_name = this_candle._alias.get(s_alias, None)
            if not s_name:
                return
        elif s_alias in l_basic:
            s_name = 'CANDLE:{}'.format(this_candle.main_key)
            s_info2 = 'CANDLE'
            s_info = s_alias

        d_data = this_candle.d_candle_data[s_name]
        if s_info2 == 'CANDLE':
            if len(d_data['data'][s_info]) > 0:
                return np.array(d_data['data'][s_info])
        else:
            if len(d_data['data']) > 0:
                return np.array(d_data['data'])
        return None

    def update(self, hist):
        '''
        Update data and check if the candle information is complete

        :param raw_data: neutrino object.
        :return: CandleData object.
        '''
        l_aux = str(hist.Indicator()).split(':')
        d_conf = dict([x.split('=') for x in l_aux[2].split(';')])
        s_name = l_aux[1]
        # s_interval = l_aux[2].split(';')[0]
        s_interval = d_conf['interval']
        # s_key = s_name + ':' + s_interval
        s_key = s_name + ':interval=' + s_interval
        obj_aux = self._data_holder.get(s_key, None)
        if isinstance(obj_aux, type(None)):
            return None
        return obj_aux.update(hist)


class CandleData(object):
    '''
    Candle Data representation
    '''
    def __init__(self, s_symbol, i_interval, i_nbars):
        '''
        Instatiate a CandleData object

        :param symbol: string. symbol to be subscribed
        :param resol: integer. The lenth of the candle, in seconds
        :param window: inter. Numb of candle to return  after the first update
        :param begin: integer. how long to recover, in seconds
        '''
        self.s_symbol = s_symbol
        self.symbol_name = s_symbol
        self.s_conf = 'interval={:0.0f}'.format(i_interval)
        self.i_interval = i_interval
        self.i_nbars = i_nbars
        self.s_name = ''
        s_key = 'CANDLE:{}:interval={:0.0f}'.format(s_symbol, i_interval)
        self.main_key = s_key.replace('CANDLE:', '')
        self.d_candle_data = {s_key: {'ID': 0, 'data': None}}
        self._last_idx = 0
        self.d_last_ts = {s_key: 0}
        self.i_count = 0
        self._alias = {}
        self.l_to_subscribe = []
        self.i_lastbgtime = 0
        # control the last tradeID used
        self.d_last_tradeid = {s_key: 0}
        self.i_last_tradeid = -1
        self.count = 1
        self.data_updated = 0
        self.v3_obj = None
        self.l_to_subscribe.append({'symbol': self.s_symbol,
                                    'what': "CANDLE",
                                    'conf': self.s_conf})

    def set_name(self, s_name):
        '''
        '''
        self.s_name = s_name

    def on_symbols_load(self, f_fxnow):
        '''
        Subscribe the indicators in the buffer

        :param f_fxnow: float. The current time, in seconds
        '''
        s_txt, i_bgt = get_begin_time(f_fxnow, self.i_nbars, self.i_interval)
        self.i_lastbgtime = i_bgt
        for d_conf in self.l_to_subscribe:
            fx.subscribeIndicator(str(d_conf['symbol']),
                                  str(d_conf['what']),
                                  str(d_conf['conf']),
                                  i_bgt)
        self.count = len(self.l_to_subscribe)
        return s_txt

    def get_value(self, s_alias, i_idx, s_info=None, f_timeperiod=None,
                  i_inner_idx=0):
        '''
        Return the desired information related to the candle. f_timeperiod and
        s_info are required just if s_alias is None

        :param s_alias: string. the alias to the information requested
        :param i_idx: integer. the index of the information in values list
        :param s_info: string. information requested
        :param f_timeperiod: float. timepreriod of the indicator
        :param i_inner_idx: integer. inner index of the information desired
        :return: float. The value of the information requested
        '''
        l_basic = ['HIGH', 'LOW', 'CLOSE', 'OPEN', 'QTY', 'VOLUME', 'TS',
                   'QTY_BUYER', 'QTY_SELLER', 'CUMQTY_SELLER', 'CUMQTY_BUYER',
                   'CUMQTY']
        # if not len(self):
        #     return None
        if s_info:
            s_info2 = s_info
            if s_info in l_basic:
                s_info2 = 'CANDLE'
                s_name = '{}:{}:'.format(s_info2, self.s_symbol) + self.s_conf
            if f_timeperiod and s_info2 != 'CANDLE':
                s_name += ';time_period={:0.0f}'.format(f_timeperiod)
        else:
            if s_alias not in l_basic:
                s_info2 = s_alias
                s_name = self._alias.get(s_alias, None)
                if not s_name:
                    return
            elif s_alias in l_basic:
                s_info2 = 'CANDLE'
                s_name = '{}:{}:'.format(s_info2, self.s_symbol) + self.s_conf
                s_info = s_alias
                if f_timeperiod and s_info2 != 'CANDLE':
                    s_name += ';time_period={:0.0f}'.format(f_timeperiod)

        d_data = self.d_candle_data[s_name]
        if s_info2 == 'CANDLE':
            if not d_data['data']:
                return None
            if not d_data['data'][s_info]:
                return None
            if len(d_data['data'][s_info]) >= abs(i_idx):
                return d_data['data'][s_info][i_idx]
        else:
            if d_data['data'] and len(d_data['data']) >= abs(i_idx):
                return d_data['data'][i_idx][i_inner_idx]
        return None

    def add_indicator(self, **kwargs):
        '''
        Add a new infdicator to the candle

        :param s_ta_name: string. Indicator name (ta-lib)
        :param i_time_period: inter. rolling windows length
        :param s_alias: string.
        :return: Boolean. If it susbcribed new data
        '''
        # SMA:PETR4:interval=60;time_period=20
        s_ta_name = kwargs.get('s_ta_name')
        i_time_period = kwargs.get('i_time_period')
        s_alias = kwargs.get('s_alias')
        s_input = kwargs.get('s_input', None)
        i_ma_period = kwargs.get('i_ma_period', None)
        # define the basic conf
        s_conf = "interval={:0.0f};time_period={:0.0f}"
        s_conf = s_conf.format(self.i_interval, i_time_period)
        # define input for TAs that accept these variables
        if not s_input:
            if s_ta_name in ['EMA', 'SMA', 'MOM', 'BBANDS', 'SAMOM', 'STDDEV',
                             'SABBANDS']:
                s_input = 'close'
        # define ma preiod for SAMOM conf
        if not i_ma_period and s_ta_name in ['SAMOM', 'SABBANDS', 'SAADX']:
            i_ma_period = 3
        if i_ma_period:
            s_conf = 'sa_period={:0.0f};{}'.format(i_ma_period, s_conf)
        # also include input in conf
        if s_input:
            s_conf = 'input=%s;%s' % (s_input, s_conf)
        # define BBANDS conf
        if s_ta_name in ['BBANDS', 'SABBANDS']:
            for s_aux, i in zip(['nbdevup', 'nbdevdn', 'matype'], [2, 2, 0]):
                i_aux = kwargs.get(s_aux, i)
                s_conf = '%s=%s;%s' % (s_aux, i_aux, s_conf)
        # define STDDEV conf
        f_nbdev = kwargs.get('nbdev', None)
        if f_nbdev and s_ta_name == 'STDDEV':
            s_conf = 'nbdev={:0.0f};{}'.format(f_nbdev, s_conf)
        # interval is not in the name because it is always the same
        s_name = '{}:{}:' + s_conf
        s_name = s_name.format(s_ta_name, self.s_symbol)
        self._alias[s_alias] = s_name
        if s_name in self.d_candle_data:
            return False
        self.d_last_ts[s_name] = 0
        self.d_last_tradeid[s_name] = -1
        self._last_idx += 1
        self.d_candle_data[s_name] = {'ID': 0, 'data': None}
        self.d_candle_data[s_name]['ID'] = self._last_idx
        self.l_to_subscribe.append({'symbol': self.s_symbol,
                                    'what': s_ta_name,
                                    'conf': s_conf})
        return True

    def update(self, hist):
        '''
        Update data and check if the candle information is complete

        :param hist: neutrino object.
        '''
        indicator = hist.Indicator()
        s_name = str(indicator)
        i_len = hist.TimestampsLength()

        # check the amount of data subscribed that is in the same tradeID
        i_tradeid = hist.LastTradeId()
        i_last_tradeid = self.d_last_tradeid[s_name]
        if i_tradeid != self.i_last_tradeid:
            self.i_last_tradeid = i_tradeid
            self.data_updated = 0
        if i_tradeid != i_last_tradeid:
            self.d_last_tradeid[s_name] = i_tradeid
        self.data_updated += (self.i_last_tradeid == i_tradeid)*1

        # update data structure
        f_interval = float(hist.Interval())
        f_begin_ts = hist.Timestamps(0)

        if isinstance(f_begin_ts, type(None)) or np.isnan(f_begin_ts):
            return False

        # calculate the initial index
        f_last_ts = self.d_last_ts[s_name]
        i_begin_idx = int(max(0, (f_last_ts - f_begin_ts)/f_interval))

        i_this_ts = hist.Timestamps(i_len-1)
        if i_this_ts > f_last_ts:
            self.d_last_ts[s_name] = i_this_ts

        if s_name not in self.d_candle_data or not i_len:
            return False
        if 'CANDLE' in s_name:
            l_keys = ['HIGH', 'LOW', 'CLOSE', 'OPEN', 'QTY', 'VOLUME', 'TS',
                      'QTY_BUYER', 'QTY_SELLER', 'CUMQTY', 'CUMQTY_BUYER',
                      'CUMQTY_SELLER']
            l_funvalues = [hist.PMax, hist.PMin, hist.PClose, hist.POpen,
                           hist.Quantity, hist.Volume, hist.Timestamps,
                           hist.QuantityBuy, hist.QuantitySell,
                           hist.QuantityAccumulated,
                           hist.QuantityBuyAccumulated,
                           hist.QuantitySellAccumulated]
            for s_key, func in zip(l_keys, l_funvalues):
                l_data = [func(i) for i in range(i_begin_idx, i_len)]
                try:
                    # if b_replace:
                    l_aux = self.d_candle_data[s_name]['data'][s_key]
                    l_aux = l_aux[:-1] + l_data
                    if s_key == 'TS':
                        self.i_count = len(l_aux)
                    self.d_candle_data[s_name]['data'][s_key] = l_aux
                    # else:
                    #     self.d_candle_data[s_name]['data'][s_key] += l_data
                except KeyError:
                    self.d_candle_data[s_name]['data'][s_key] = l_data
                except TypeError:
                    self.d_candle_data[s_name]['data'] = {}
                    self.d_candle_data[s_name]['data'][s_key] = l_data
        else:
            i_len2 = hist.Result(0).IndicatorLength()
            i_len3 = hist.ResultLength()
            if i_len2 != i_len:
                l_data = [[None] for i in range(i_begin_idx, i_len)]
            else:
                # TODO: include treatmet to hist.Result(0).IndicatorLength == 0
                # pdb.set_trace()
                l_data = [[hist.Result(j).Indicator(i) for j in xrange(i_len3)]
                           for i in range(i_begin_idx, i_len)]
            try:
                l_aux = self.d_candle_data[s_name]['data']
                l_aux = l_aux[:-1] + l_data
                self.d_candle_data[s_name]['data'] = l_aux
            except TypeError:
                self.d_candle_data[s_name]['data'] = l_data

        # return self.d_candle_data[s_name]['ID'] == self._last_idx
        b_all_updated = self.data_updated == self.count
        if b_all_updated:
            self.data_updated = 0
        return b_all_updated

    def __str__(self):
        '''
        Return a string representation of this candle
        '''
        s_rtn = 'CANDLES({}: {} seconds)'.format(self.s_symbol, self.s_conf)
        return s_rtn

    def __len__(self):
        '''
        Return the lenght of the data stored in this class
        '''
        return self.i_count

    def __eq__(self, other):
        '''
        Check the name of the candle aginst a string
        '''
        return self.s_name == other

    def __ne__(self, other):
        '''
        Check the name of the candle aginst a string
        '''
        return self.s_name != other


class BookSideHandler(object):
    '''
    Handle interactions to a neutrino BookSide object
    '''
    def get_book_side(self, instrument=None, book=None):
        '''
        Return the neutrino BookSide related to this object

        :param instrument: Instrument object.
        :param book: BookHandler object.
        :return: neutrino BookSide Object
        '''
        raise NotImplementedError

    def by_price(self, instrument, i_depth, book=None, b_aslist=True):
        '''
        Return the book aggregated by price as a iterator of TradeInfo tuples

        :param instrument: Instrument object.
        :param i_depth: integer. Maximum Depth.
        :param *book: BookHandler object.
        :param *b_aslist: Boolean. If should return the informario as list
        :return: iterator (or list) of TradeInfo tuples.
        '''
        book_side = self.get_book_side(instrument, book=book)
        price_group = neutrino.byPrice(book_side, i_depth)
        if not book_side or not price_group:
            return [PriceLevelInfo(None, 0)]
        i_len = len(price_group)
        if not i_len:
            return [PriceLevelInfo(None, 0)]
        if b_aslist:
            l = [PriceLevelInfo(price_group[i].price, price_group[i].quantity)
                 for i in range(i_len)]
            return l

        def iter_func(price_group, i_len):
            for i in range(i_len):
                yield PriceLevelInfo(price_group[i].price,
                                     price_group[i].quantity)
        return iter_func(price_group, i_len)

    def by_order(self, instrument, book=None, i_max_len=None, b_aslist=False):
        '''
        Return all the book side information as a iterator of OrderInfo tuples

        :param instrument: Instrument object.
        :param *book: BookHandler object.
        :param *i_max_len: integer. The maximum number of orders to return
        :param *b_aslist: boolean. If should return the informario as list.
            if it is set to True, the i_max_len also should be set
        :return: iterator (or list) of OrderInfo tuples.
        '''
        book_side = self.get_book_side(instrument, book=book)
        if not book_side:
            return None
        i_len = len(book_side)
        if not i_len:
            return None
        # set the maximum orders list lenght
        if i_max_len and i_max_len < i_len:
            i_len = i_max_len
        if i_max_len and b_aslist:
            l = [OrderLevelInfo(book_side[i].price, book_side[i].quantity,
                                book_side[i].orderID,  book_side[i].detail)
                 for i in range(i_len)]
            return l

        def iter_func(book_side, i_len):
            for i in range(i_len):
                obj = book_side[i]
                yield OrderLevelInfo(obj.price, obj.quantity, obj.orderID,
                                     obj.detail)
        return iter_func(book_side, i_len)

    def price_on_level(self, instrument, i_depth, book=None, b_qty=False):
        '''
        Return the price on the level specified. If it is asked a price on a
        level more profound than the book, return the most profound price.

        :param instrument: Instrument object.
        :param i_depth: integer. Depth to be checked
        :param *book:BookHandler Object.
        :param *b_qty: boolean. If should return the total qty in the price
        :return: float. The price required
        '''
        f_price = None
        i_qty = 0
        for x in self.by_price(instrument, i_depth, book=book):
            f_price = x.price
            i_qty = x.qty
        if b_qty:
            return f_price, i_qty
        return f_price

    def best_queue(self, instrument, book=None):
        '''
        Return the PriceLevelInfo in the best price of the book side

        :param instrument: Instrument object.
        :param *book:BookHandler Object.
        :return PriceLevelInfo tuple.
        '''
        for x in self.by_price(instrument, 1, book=book):
            return x


class BidSideHandler(BookSideHandler):
    '''BidSide Handler'''
    def get_book_side(self, instrument, book=None):
        if not book:
            book = fx.book(instrument.symbol_name)
        if not book:
            return None
        return book.bid()


class AskSideHandler(BookSideHandler):
    '''AskSide Handler'''
    def get_book_side(self, instrument, book=None):
        if not book:
            book = fx.book(instrument.symbol_name)
        if not book:
            return None
        return book.ask()


class BookHandler(object):
    '''
    A wrapper to neutrino Book class
    '''

    def __init__(self):
        '''
        Instantiate a BookHandler object
        '''
        self.owner = None
        self.bid = BidSideHandler()
        self.ask = AskSideHandler()

    def set_owner(self, agent):
        '''
        Set the BookHandler owner
        '''
        self.agent = agent

    def subscribe(self, s_symbol, **kwargs):
        '''
         Subscribe the instrument desidered

         :param s_symbol: string. the instrument to subscribe
         :param *ords_stack_size: integer. to book. size of order stack
        '''
        if s_symbol not in self.agent._instr_from_conf:
            raise SymbolSubscriptionError('%s not in conf file' % s_symbol)
        if s_symbol not in self.agent._instr:
            ords_stack_size = kwargs.get('ords_stack_size', 100)
            self.agent._instr.append(s_symbol)
            this_instrument = Instrument(s_symbol, ords_stack_size)
            self.agent._instr_stack[s_symbol] = this_instrument
            return this_instrument

    def best_queues(self, instrument):
        '''
        Return the PriceLevelInfo of the best books of the instrument

        :param instrument: Instrument object.
        :return: PriceLevelInfo
        '''
        book = fx.book(instrument.symbol_name)
        if not book:
            return ((None, None), (None, None))
        t_bid = self.bid.best_queue(instrument, book)
        t_ask = self.ask.best_queue(instrument, book)
        return t_bid, t_ask

    def best_bid(self, instrument):
        '''
        Return the PriceLevelInfo of the best bid queue of the instrument

        :param instrument: Instrument object.
        :return: PriceLevelInfo
        '''
        book = fx.book(instrument.symbol_name)
        if not book:
            return (None, None)
        t_bid = self.bid.best_queue(instrument, book)
        return t_bid

    def best_ask(self, instrument):
        '''
        Return the PriceLevelInfo of the best ask queue of the instrument

        :param instrument: Instrument object.
        :return: PriceLevelInfo
        '''
        book = fx.book(instrument.symbol_name)
        if not book:
            return (None, None)
        t_ask = self.ask.best_queue(instrument, book)
        return t_ask

    def is_online(self, instrument):
        '''
        Return is the book is online or not

        :param instrument: Instrument object.
        :return: Boolean
        '''
        book = fx.book(instrument.symbol_name)
        if (book and fx.isOnline(book.name())):
            return True
        return False

    def best_price(self, instrument, s_side):
        '''
        Return the PriceLevelInfo of the best ask queue of the instrument

        :param instrument: Instrument object.
        :param s_side: string. BID or ASK
        :return: PriceLevelInfo
        '''
        if s_side == 'BID':
            best_bid = self.bid.get_book_side(instrument)
            if not best_bid:
                return None
            return best_bid[0].price
        elif s_side == 'ASK':
            best_ask = self.ask.get_book_side(instrument)
            if not best_ask:
                return None
            return best_ask[0].price

    def last_trades(self, instrument, b_aslist=False):
        '''
        Return all the trades that had occured since the last on_book_update
        as a iterator or a list

        :param instrument: Instrument object.
        :param *b_aslist: boolean. If should return the informario as list.
        :return: iterator (or list) of TradeInfo tuples.
        '''
        book = fx.book(instrument.symbol_name)
        if not book:
            return []
        trades = fx.getTrades(book)
        summary = fx.getSummary(book)
        if isinstance(summary.tradeCount, type(None)):
            return []
        i_iterate = len(trades) - summary.tradeCount

        if b_aslist:
            l = [TradeInfo(trades[idx].price, trades[idx].quantity,
                           trades[idx].buyer, trades[idx].seller,
                           trades[idx].time, trades[idx].status,
                           trades[idx].tradeID)
                 for idx in range(max(0, i_iterate), len(trades))]
            if l:
                instrument.last_trade = l[-1]
            return l

        def iter_func(trades, i_iterate, instrument):
            for idx in range(max(0, i_iterate), len(trades)):
                obj_rtn = TradeInfo(trades[idx].price, trades[idx].quantity,
                                    trades[idx].buyer, trades[idx].seller,
                                    trades[idx].time, trades[idx].status,
                                    trades[idx].tradeID)
                instrument.last_trade = obj_rtn
                yield obj_rtn
        return iter_func(trades, i_iterate, instrument)

    def last_trade_buffered(self, instrument):
        '''
        Return the last tradeinformation

        :param instrument: Instrument object.
        :return: TradeInfo tuples.
        '''
        return instrument.last_trade

    def last_traded_price(self, instrument):
        '''
        Return the last traded price that has occured

        :param instrument: Instrument object.
        :return: float.
        '''
        book = fx.book(instrument.symbol_name)
        if not book:
            return None
        trades = fx.getTrades(book)
        idx = len(trades)
        if not idx:
            return None
        idx -= 1
        obj_rtn = TradeInfo(trades[idx].price, trades[idx].quantity,
                            trades[idx].buyer, trades[idx].seller,
                            trades[idx].time, trades[idx].status,
                            trades[idx].tradeID)
        instrument.last_trade = obj_rtn
        return obj_rtn.price

    def sequence(self, instrument):
        '''
        Return the current sequence number of the book

        :param instrument: Instrument object.
        '''
        return fx.book(instrument.symbol_name).sequence()

    def last_counts(self, instrument):
        '''
        Return the last counts since the last book update

        :param instrument: Instrument object.
        :return: CountsInfo object.
        '''
        # simulation

        if not PROD:
            summary = fx.getSummary(fx.book(instrument.symbol_name), True)
            obj_rtn = CountsInfo(summary.bidCount,
                                 summary.askCount,
                                 summary.tradeCountIncrement,
                                 summary.newBidOrders,
                                 summary.canceledBidOrders,
                                 summary.replacedBidOrders,
                                 summary.newAskOrders,
                                 summary.canceledAskOrders,
                                 summary.replacedAskOrders,
                                 summary.statusChanged)
        # production
        else:
            summary = fx.getSummary(fx.book(instrument.symbol_name))
            obj_rtn = CountsInfo(summary.bidCount, summary.askCount,
                                 summary.tradeCount, 0, 0, 0, 0, 0, 0,
                                 summary.statusChanged)
        return obj_rtn
