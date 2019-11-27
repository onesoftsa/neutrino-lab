#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Implement auxiliary classes and functions used by an agent


@author: ucaiado

Created on 07/05/2018
'''

# agent imports
from __future__ import print_function
import os
import json
import yaml
import datetime
import calendar
import time
from enum import Enum
import numpy as np

from neutrinogym.qcore import PROD

if not PROD:
    import neutrinogym.neutrino as neutrino
    from neutrinogym.neutrino import fx
    convert_time = datetime.datetime.utcfromtimestamp  # simulation
else:
    import neutrino
    from neutrino import fx
    convert_time = datetime.datetime.fromtimestamp  # production?

'''
Begin help functions
'''


'''
End help functions
'''


class DoubleWrapperError(Exception):
    '''
    DoubleWrapperError is raised by the Wrapper class to indicate that
    the Agent class passed is already wrapped
    '''
    pass


class SymbolSubscriptionError(Exception):
    '''
    SymbolSubscriptionError is raised by the agent class to indicate that
    ithe instrument that it is tryint to subcribe is not in the configuration
    file
    '''
    pass


class SubscrType(Enum):
    BOOK = 0
    CANDLES = 1

    def __eq__(self, o):
        if isinstance(o, SubscrType):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name


class CandleIntervals(Enum):
    MIN_1 = 60
    MIN_2 = 120
    MIN_3 = 180
    MIN_5 = 300
    MIN_10 = 600
    MIN_15 = 900
    MIN_30 = 1800
    HOUR_1 = 3600
    DAY_1 = 3600*24

    def __eq__(self, o):
        if isinstance(o, SubscrType):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name


if not PROD:
    def neutrino_now(b_str=False, b_ts=False, s_time=False, f_time=False,
                     b_utc=False):
        '''
        Return the current time, dealing with the differences of consulting
        fx.now in production and simulation environment

        :param b_str: boolean. return as string
        :param b_ts: boolean. return as seconds based on timestamp
        :param s_time: string. return the time passed as seconds
        '''
        # simulation
        if s_time:
            return sum([float(x)*60**(2-i) for i, x
                        in enumerate(s_time.split(':'))])
        if f_time:
            i_hour = int(f_time)/60**2
            i_min = int(f_time - i_hour*60**2)/60
            i_seconds = int(f_time - i_hour*60**2 - i_min*60.)
            s_rtn = '{:02d}:{:02d}:{:02d}'.format(i_hour, i_min, i_seconds)
            return s_rtn
        if b_ts:
            return fx.now(b_ts=True)
        if b_str:
            return fx.now(b_str=True)
        return fx.now()

else:
    def neutrino_now(b_str=False, b_ts=False, s_time=False, f_time=False,
                     b_utc=False):
        '''
        Return the current time, dealing with the differences of consulting
        fx.now in production and simulation environment

        :param b_str: boolean. return as string
        :param b_ts: boolean. return as seconds based on timestamp
        :param s_time: string. return the time passed as seconds
        '''
        # production
        if s_time:
            s_aux = time.strftime('%m/%d/%Y ', time.localtime(fx.now()))
            s_format = '%m/%d/%Y %H:%M:%S'
            obj_aux = time.strptime(s_aux + s_time, s_format)
            if b_utc:
                return calendar.timegm(obj_aux)
            return time.mktime(obj_aux)
        if f_time:
            s_format = '%H:%M:%S'
            s_aux = time.strftime(s_format, time.localtime(f_time))
            return s_aux
        if b_ts:
            return fx.now()
        if b_str:
            f_time = fx.now()
            s_format = '%m/%d/%Y %H:%M:%S'
            s_aux = time.strftime(s_format, time.localtime(f_time))
            s_aux += '{:0.3f}'.format(f_time-int(f_time))[1:]
            return s_aux
            # return str(fx.now())
        return fx.now()


class Logger(object):
    def __init__(self, d_logs):
        self.logs = d_logs

    def print(self, s_msg):
        print(s_msg)

    def __getitem__(self, s_key):
        return self.logs[s_key]


def get_begin_time(fx_now, bar_count, bar_interval):
    '''
    Return the begin time, in seconds, based on the bar count passed and the
    time interval of each bar. Assume that each market session opens at 9 AM
    and close at 18 PM. Also, take into account business days

    :param fx_now: float. Unix timestamp
    :param bar_count: integer.
    :param bar_interval: integer.
    '''
    # initiate variables
    fx_now = neutrino_now(b_ts=True)
    func = datetime.datetime.strptime
    s_path = os.path.dirname(os.path.realpath(__file__))
    na_dates = np.genfromtxt(s_path + '/du.txt',
                             delimiter=',',
                             dtype=object,
                             skip_header=1,
                             converters={0: lambda x: func(x, '%m/%d/%Y')})
    i_total_session_bars = int(1 + (18-10)*60**2/bar_interval)

    dt_now = convert_time(fx_now)
    # bound the date
    dt_min = datetime.datetime(dt_now.year, dt_now.month, dt_now.day, 10, 0)
    dt_max = datetime.datetime(dt_now.year, dt_now.month, dt_now.day, 18, 0)
    dt_now = min(max(dt_now, dt_min), dt_max)
    na_idx = np.where(na_dates < dt_now)[0]
    # how many bars are today
    f_sec_today = (dt_now.hour-10)*3600+dt_now.minute*60+dt_now.second
    i_total_today_bars = int(np.ceil(f_sec_today*1./bar_interval))
    # how many days It needs
    # i_penalty_bars = max(0, i_total_today_bars - i_total_session_bars)
    f_days_offset = (bar_count-min(i_total_session_bars, i_total_today_bars))
    f_days_offset *= 1.
    f_days_offset /= i_total_session_bars
    f_remain_time = (1 - (f_days_offset) % 1)
    f_remain_time *= i_total_session_bars * bar_interval
    if f_remain_time == i_total_session_bars * bar_interval:
        f_remain_time = 0

    # how many hours it still needs to account
    i_hours = int(f_remain_time / 3600)
    i_minutes = (f_remain_time - i_hours*3600)/60

    # f_days_offset = 2

    dt_rtn = na_dates[na_idx[min(-1, -1-int(np.ceil(f_days_offset)))]]
    dt_rtn += datetime.timedelta(hours=i_hours+10, minutes=i_minutes)
    # dt_rtn += datetime.timedelta(hours=5, minutes=30)
    s_rtn = 'get_begin_time - recover data from %s' % dt_rtn
    i_rtn = int((dt_rtn-datetime.datetime(1970, 1, 1)).total_seconds())
    return s_rtn, i_rtn
