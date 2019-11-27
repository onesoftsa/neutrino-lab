#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Implement an agent interface to interact with Neutrino API and simulate the
enrionemnt to allow testing the strategies created

@author: ucaiado

Created on 05/17/2018
'''

from collections import deque
import itertools
import numpy as np
import talib
from neutrinogym.neutrino import fx

import pdb

'''
Begin help functions
'''

LAST_TIME = 0
MAP_INPUT = {'pmax': 'na_max',
             'pmin': 'na_min',
             'open': 'na_open',
             'close': 'na_close',
             'quantity': 'na_qty',
             'quantity_sell': 'na_qtys',
             'quantity_buy': 'na_qtyb',
             'quantity_accumulated': 'na_cumqty',
             'quantity_sell_accumulated': 'na_cumqtys',
             'quantity_buy_accumulated': 'na_cumqtyb'}


def same_val(f_value, f_old):
    return f_value


def acum(f_value, f_old):
    try:
        return f_value + f_old
    except TypeError:
        print('f_value ', f_value)
        print('f_old ', f_old)
        raise TypeError


def extend_ts(f_old, f_elapsed_time, i_include):
    f_old2 = f_old + f_elapsed_time
    f_limit = (f_old+i_include*f_elapsed_time + 1)
    obj_aux = itertools.count(f_old2, f_elapsed_time)
    gen = itertools.takewhile(lambda n: n < f_limit, obj_aux)
    return gen


def extend_all(f_old, f_elapsed_time, i_include):
    return itertools.repeat(f_old, i_include)


def update_ADX(**kwargs):
    na_rtn = talib.ADX(kwargs.get('na_max'),
                       kwargs.get('na_min'),
                       kwargs.get('na_close'),
                       timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_SAADX(**kwargs):
    na_aux = talib.ADX(kwargs.get('na_max'),
                       kwargs.get('na_min'),
                       kwargs.get('na_close'),
                       timeperiod=kwargs.get('i_timeperiod'))

    if (~np.isnan(na_aux)).any():
        i_maperiod = kwargs.get('d_conf').get('sa_period', None)
        if i_maperiod:
            i_maperiod = int(i_maperiod)
        na_aux = talib.SMA(na_aux, timeperiod=i_maperiod)
    return np.array([na_aux])


def update_SATR(**kwargs):

    na_tr = talib.TRANGE(kwargs.get('na_max'),
                         kwargs.get('na_min'),
                         kwargs.get('na_close'))
    if not (~np.isnan(na_tr)).any():
        return None
    na_rtn = talib.SMA(na_tr, timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_TRANGE(**kwargs):

    na_tr = talib.TRANGE(kwargs.get('na_max'),
                         kwargs.get('na_min'),
                         kwargs.get('na_close'))
    if not (~np.isnan(na_tr)).any():
        return None
    return np.array([na_tr])


def update_ATR(**kwargs):
    na_rtn = talib.ATR(kwargs.get('na_max'),
                       kwargs.get('na_min'),
                       kwargs.get('na_close'),
                       timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_PLUS_DI(**kwargs):
    na_rtn = talib.PLUS_DI(kwargs.get('na_max'),
                           kwargs.get('na_min'),
                           kwargs.get('na_close'),
                           timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_MINUS_DI(**kwargs):
    na_rtn = talib.MINUS_DI(kwargs.get('na_max'),
                            kwargs.get('na_min'),
                            kwargs.get('na_close'),
                            timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])

def update_BBANDS(**kwargs):
    na_rtn = talib.BBANDS(kwargs.get('na_close'),
                          nbdevup=float(kwargs.get('d_conf').get('nbdevup')),
                          nbdevdn=float(kwargs.get('d_conf').get('nbdevdn')),
                          matype=int(kwargs.get('d_conf').get('matype')),
                          timeperiod=kwargs.get('i_timeperiod'))
    # return np.stack(na_rtn, 1)
    return np.stack(na_rtn)

def update_SABBANDS(**kwargs):
    na_aux = talib.BBANDS(kwargs.get('na_close'),
                          nbdevup=float(kwargs.get('d_conf').get('nbdevup')),
                          nbdevdn=float(kwargs.get('d_conf').get('nbdevdn')),
                          matype=int(kwargs.get('d_conf').get('matype')),
                          timeperiod=kwargs.get('i_timeperiod'))
    na1, na2, na3 = na_aux
    if (~np.isnan(na2)).any():
        i_maperiod = kwargs.get('d_conf').get('sa_period', None)
        if i_maperiod:
            i_maperiod = int(i_maperiod)
        na_rtn = (talib.SMA(na1, timeperiod=i_maperiod),
                  talib.SMA(na2, timeperiod=i_maperiod),
                  talib.SMA(na3, timeperiod=i_maperiod))
        # return np.stack(na_rtn, 1)
        return np.stack(na_rtn)
    # return np.stack(na_aux, 1)
    return np.stack(na_aux)


def update_MOM(**kwargs):
    na_values = kwargs.get('na_close')
    if 's_input' in kwargs:
        na_values = kwargs.get(MAP_INPUT[kwargs.get('s_input')])
    if len(na_values) < 2:
        return na_values[0]
    na_values = na_values.astype('float64')
    na_rtn = talib.MOM(na_values, timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_SAMOM(**kwargs):
    na_values = kwargs.get('na_close')
    if 's_input' in kwargs:
        na_values = kwargs.get(MAP_INPUT[kwargs.get('s_input')])
    if len(na_values) < 2:
        return na_values[0]
    na_values = na_values.astype('float64')
    na_mom = talib.MOM(na_values, timeperiod=kwargs.get('i_timeperiod'))
    if (~np.isnan(na_mom)).any():
        i_maperiod = kwargs.get('d_conf').get('sa_period', None)
        if i_maperiod:
            i_maperiod = int(i_maperiod)
        na_mom = talib.SMA(na_mom, timeperiod=i_maperiod)
    return np.array([na_mom])


def update_SMA(**kwargs):
    na_values = kwargs.get('na_close')
    if 's_input' in kwargs:
        na_values = kwargs.get(MAP_INPUT[kwargs.get('s_input')])
    if len(na_values) < 2:
        return na_values[0]
    na_values = na_values.astype('float64')
    na_rtn = talib.SMA(na_values, timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_EMA(**kwargs):
    na_values = kwargs.get('na_close')
    if 's_input' in kwargs:
        na_values = kwargs.get(MAP_INPUT[kwargs.get('s_input')])
    if len(na_values) < 2:
        return np.array([na_values[0]])
    na_values = na_values.astype('float64')
    na_rtn = talib.EMA(na_values, timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


def update_STDDEV(**kwargs):
    na_values = kwargs.get('na_close')
    if 's_input' in kwargs:
        na_values = kwargs.get(MAP_INPUT[kwargs.get('s_input')])
    if not (~np.isnan(na_values)).any():
        return None
    na_values = na_values.astype('float64')
    f_nbdev = kwargs.get('d_conf').get('nbdev', None)
    if f_nbdev:
        f_nbdev = float(f_nbdev)
    na_rtn = talib.STDDEV(na_values,
                          nbdev=f_nbdev,
                          timeperiod=kwargs.get('i_timeperiod'))
    return np.array([na_rtn])


'''
End help functions
'''

TA_UPDATE_MAP = {'SMA': update_SMA,
                 'SATR': update_SATR,
                 'ATR': update_ATR,
                 'SAADX': update_SAADX,
                 'ADX': update_ADX,
                 'TRANGE': update_TRANGE,
                 'PLUS_DI': update_PLUS_DI,
                 'MINUS_DI': update_MINUS_DI,
                 'SAMOM': update_SAMOM,
                 'MOM': update_MOM,
                 'EMA': update_EMA,
                 'BBANDS': update_BBANDS,
                 'SABBANDS': update_SABBANDS,
                 'STDDEV': update_STDDEV
                 }


def update_prices(d_instr_data, f_value, f_time):
    '''
    Update price lists of the given instrument

    :param f_value: float. value to be kept
    :param f_time: float. Time in seconds
    '''
    f_aux = d_instr_data['LST'].get_value()
    b_update = False
    if not f_value:
        f_value = f_aux
    for s_key, f_val in zip(['MAX', 'MIN', 'LST'], [f_aux, f_aux, None]):
        if d_instr_data[s_key].update(f_value, f_time, f_val):
            b_update = True
            d_instr_data[s_key].repeat_the_last(f_time, f_val)
    return d_instr_data, b_update


def aux_update_cumqty(s_key, d_instr_data, f_value, f_time):
    f_lastval = d_instr_data[s_key].get_value(-1)
    i_len = d_instr_data[s_key].count
    if d_instr_data[s_key].update(f_value, f_time, f_lastval):
        if i_len != d_instr_data[s_key].count and i_len > 0:
            d_instr_data[s_key].update(f_lastval, f_time, 0)
        d_instr_data[s_key].repeat_the_last(f_time, 0)


def update_qty(d_instr_data, f_value, f_time, s_agr):
    '''
    Update qty lists of the given instrument

    :param f_value: float. value to be kept
    :param f_time: float. Time in seconds
    '''
    f_val = 0
    f_valb = 0
    f_vals = 0
    b_update = False
    # update qty
    if not f_value:
        f_value = 0
    if d_instr_data['QTD'].update(f_value, f_time, f_val):
        b_update = True
        d_instr_data['QTD'].repeat_the_last(f_time, f_val)
    aux_update_cumqty('CUMQTD', d_instr_data, f_value, f_time)

    # update number of trades
    if d_instr_data['NTRADES'].update(1, f_time, f_val):
        b_update = True
        d_instr_data['NTRADES'].repeat_the_last(f_time, f_val)

    # update agressor
    if s_agr == '+':
        f_valb = f_value
    if d_instr_data['QTD_B'].update(f_valb, f_time, f_val):
        d_instr_data['QTD_B'].repeat_the_last(f_time, f_val)
    aux_update_cumqty('CUMQTD_B', d_instr_data, f_valb, f_time)

    if s_agr == '-':
        f_vals = f_value
    if d_instr_data['QTD_S'].update(f_vals, f_time, f_val):
        d_instr_data['QTD_S'].repeat_the_last(f_time, f_val)
    aux_update_cumqty('CUMQTD_S', d_instr_data, f_vals, f_time)

    return d_instr_data, b_update


def update_ts(d_instr_data, f_value, f_time):
    '''
    Update price lists of the given instrument

    :param f_value: float. value to be kept
    :param f_time: float. Time in seconds
    '''
    f_val = d_instr_data['TS'].get_value()
    if d_instr_data['TS'].update(f_value, f_time, f_val):
        # print 'update_ts():', f_value, f_time, fx.now(True)
        d_instr_data['TS'].repeat_the_last(f_time, f_val)
    return d_instr_data


def update_volume(d_instr_data, f_value, f_time):
    '''
    Update price lists of the given instrument

    :param f_value: float. value to be kept
    :param f_time: float. Time in seconds
    '''
    f_val = 0
    if not f_value:
        f_value = 0
    if d_instr_data['VOLUME'].update(f_value, f_time, f_val):
        d_instr_data['VOLUME'].repeat_the_last(f_time, f_val)
    return d_instr_data


def update_ta(b_update, d_instr_data):
    # update TA indicators
    b_there_is_ta = len(d_instr_data) > 5
    if b_update and b_there_is_ta:
        na_close = np.array(d_instr_data['LST'].l)
        na_max = np.array(d_instr_data['MAX'].l)
        na_min = np.array(d_instr_data['MIN'].l)
        na_qty = np.array(d_instr_data['QTD'].l)
        na_qtyb = np.array(d_instr_data['QTD_B'].l)
        na_qtys = np.array(d_instr_data['QTD_S'].l)
        na_cumqty = np.array(d_instr_data['CUMQTD'].l)
        na_cumqtyb = np.array(d_instr_data['CUMQTD_B'].l)
        na_cumqtys = np.array(d_instr_data['CUMQTD_S'].l)

        for s_this_ta in d_instr_data['INDICATORS']:
            s_ta_key, s_cmm, s_aux = s_this_ta.split(':')
            d_conf = dict([x.split('=') for x in s_aux.split(';')])
            i_time_period = int(d_conf['time_period'])
            # l_aux = s_this_ta.split(';')
            # i_time_period = int(l_aux[-1].split('=')[1])
            # s_ta_key = l_aux[0].split(':')[0]
            s_input = None
            if s_ta_key in ['SMA', 'EMA', 'STDDEV', 'MOM', 'SAMOM']:
                s_input = d_conf.get('input', None)
                if not s_input:
                    s_input = 'close'
            na_aux = TA_UPDATE_MAP[s_ta_key](na_max=na_max,
                                             na_min=na_min,
                                             na_close=na_close,
                                             na_qty=na_qty,
                                             na_qtyb=na_qtyb,
                                             na_qtys=na_qtys,
                                             na_cumqty=na_cumqty,
                                             na_cumqtyb=na_cumqtyb,
                                             na_cumqtys=na_cumqtys,
                                             s_input=s_input,
                                             d_conf=d_conf,
                                             i_timeperiod=i_time_period)
            d_instr_data[s_this_ta] = na_aux
    return d_instr_data


def make_updates(symbol, d_inst_data):
    '''
    ...

    :param symbol: string.
    :param inst_data: dict.
    '''
    global LAST_TIME

    trades = fx.getTrades(fx.book(symbol), True)
    summary = fx.getSummary(fx.book(symbol), True)
    f_mkt_time = fx.now(b_old=True)
    d_update = {}
    for s_name in d_inst_data:
        inst_data = d_inst_data[s_name]
        f_price = None
        last_trade_id = inst_data['ID']
        if isinstance(summary.tradeCount, type(None)):
            return f_price
        # for obj_trade in trades:
        i_iterate = len(trades) - summary.tradeCount
        d_update[s_name] = False
        b_update = False
        for idx in range(max(0, i_iterate), len(trades)):
            obj_trade = trades[idx]
            s_agr = obj_trade.status
            f_price = obj_trade.price
            f_qty = obj_trade.quantity
            i_id = obj_trade.tradeID
            # s = str(obj_trade.time/1000.)
            s = '{0:09d}'.format(obj_trade.time)
            s = s[:-3] + '.' + s[-3:]
            if s_agr not in ['+', '-', 'X'] or i_id <= last_trade_id:
                continue
            inst_data['ID'] = i_id
            f_time2 = float(s[:2])*60**2+float(s[2:4])*60 + float(s[4:])
            inst_data, b_update = update_prices(inst_data, f_price, f_time2)
            inst_data, b_update2 = update_qty(inst_data, f_qty, f_time2, s_agr)
            inst_data = update_volume(inst_data, f_qty*f_price, f_time2)
            f_last_time = inst_data['LST'].last_time
            inst_data = update_ts(inst_data, f_last_time, f_time2)
            b_update = b_update or b_update2
            inst_data = update_ta(b_update, inst_data)
            d_update[s_name] = b_update
        # ensure that the candle data is updated at least one time per 10 secds
        if not b_update and (f_mkt_time - LAST_TIME) >= 10:  # not correct
            LAST_TIME = f_mkt_time
            # print 'make_updates(): try to update by time', fx.now(True)
            inst_data, b_update = update_prices(inst_data, None, f_mkt_time)
            inst_data, b_update2 = update_qty(inst_data, None, f_mkt_time, 'X')
            inst_data = update_volume(inst_data, None, f_mkt_time)
            b_update = b_update or b_update2
            d_update[s_name] = b_update
            f_last_time = inst_data['LST'].last_time
            inst_data = update_ts(inst_data, f_last_time, f_mkt_time)
            inst_data = update_ta(b_update, inst_data)

    # print inst_data
    # raise NotImplementedError()
    return d_update, d_inst_data


class ElapsedList(object):
    '''
    ElapsedList is a list that has a maximum lenght and is updated from time
    to time
    '''

    _compare = {'MAX': max, 'MIN': min, 'LST': same_val, 'QTD': acum,
                'VOLUME': acum, 'TS': same_val, 'QTD_B': acum,
                'QTD_S': acum, 'CUMQTD': acum, 'CUMQTD_B': acum,
                'CUMQTD_S': acum, 'NTRADES': acum}

    _extend = {'MAX': extend_all, 'MIN': extend_all, 'LST': extend_all,
               'QTD': extend_all, 'QTD_B': extend_all, 'QTD_S': extend_all,
               'VOLUME': extend_all, 'TS': extend_ts, 'CUMQTD': extend_all,
               'CUMQTD_B': extend_all, 'CUMQTD_S': extend_all,
               'NTRADES': extend_all}

    def __init__(self, f_elapsed_time=1., i_count=30, s_type='LST'):
        '''
        Initialize an ElapsedList object. Save all parameters as attributes
        :param f_elapsed_time: float. time resolution in seconds. It is how
            much information you lose at the begining of each time bucket
        :param i_count: the maximum size of the list kept in memory. i_count
            times f_elapsed_time is the time you are interested in
        '''
        self.b_already_used = False
        self.i_count = i_count
        self.f_elapsed_time = max(1., f_elapsed_time)
        self.last_time = 0.
        self.l = deque([], maxlen=i_count)
        self.i_used = 0
        self.compare = self._compare[s_type]
        self.s_type = s_type

    def update(self, f_value, f_current_time, f_valrepeat=None):
        '''
        Update the list according to the time passed. Return if it changed
        prices in the list

        :param f_current_time: float. the curent time, in seconds
        :param f_value: Python object. Any python structure to be inserted
        '''
        self.i_used += 1
        f_elapsed_time = self.f_elapsed_time
        f_time = self.last_time + f_elapsed_time
        # if it is the first time or change bucket
        if f_current_time >= f_time or self.i_used == 1:
            f_aux = int(self.last_time/f_elapsed_time+1)
            f_aux *= f_elapsed_time
            f_aux = int((f_current_time - f_aux)/f_elapsed_time)
            # if int(min(f_aux, self.i_count)) > 500:
            #     import pdb; pdb.set_trace()
            i_include = int(min(f_aux, self.i_count))
            # i_include = f_aux
            if i_include > 0 and self.i_used != 1:
                f_old = self.l[-1]
                if f_valrepeat or f_valrepeat == 0:
                    f_old = f_valrepeat
                g = self._extend[self.s_type](f_old, f_elapsed_time, i_include)
                self.l.extend(g)
            self.l.append(f_value)
            f_aux = int(f_current_time/f_elapsed_time) * f_elapsed_time
            self.last_time = f_aux
            return True
        else:
            if f_current_time < self.last_time:
                return False
            f_old = self.l[-1]
            if not f_old:
                f_old = 0
            self.l[-1] = self.compare(f_value, f_old)
            return f_old != self.l[-1]

    def repeat_the_last(self, f_current_time, f_valrepeat=None):
        '''
        Repeat the last value using the time passed
        '''
        try:
            f_old = self.l[-1]
            f_other = None
            if f_valrepeat:
                f_other = f_valrepeat
            if f_valrepeat == 0:
                f_other = 0
                f_old = 0
            if not f_other:
                f_other = 0
            return self.update(f_old, f_current_time, f_other)
        except IndexError:
            return False

    def get_value(self, i_id=None):
        '''
        Return and item from the list according to the id passed
        '''
        try:
            if not i_id:
                return self.l[-1]
            return self.l[i_id]
        except IndexError:
            return None

    def get_last_values(self, i_id=None):
        '''
        Return and item from the list according to the id passed
        '''
        # try:
        if i_id:
            return self.l[i_id]
        if not self.l:
            return None
        return list(self.l)[0]
        # except IndexError:
        #     return None

    def get_last_values_as_array(self):
        '''
        Return the values already in memory as a numpy array
        '''
        return np.array(self.get_last_values())

    def get_values(self):
        '''
        Return the values already in memory as a numpy array
        '''
        return np.array(self.l)

    def get_current_bucket(self):
        '''
        Return the last_time attribute
        '''
        return self.last_time

    @property
    def count(self):
        '''
        Return and item from the list according to the id passed
        '''
        return len(self.l)
