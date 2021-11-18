#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
...

@author: fertesta, ucaiado

Created on 01/05/2018
'''

from enum import Enum
import datetime
import random
from collections import namedtuple
import numpy as np

ENV = None
BOVESPA = False
CALLBACKS = {}


class NoneObjectError(Exception):
    """
    NoneObjectError is raised by the BandRegister and IndicatorRegister object
    after they are removed using remove_indicator() bar method
    """
    pass


def init_pending_cbacks():
    return {
        'trade': [], 'book': [], 'other': [], 'candle': [], 'checked': False}


def gen_uuid(size=16):
    '''
    '''
    random.seed()
    table = 'abcdefghijklmnopqrstuvxwyzABCDEFGHIJKLMNOPQRSTUVXWYZ0123456789'
    table_size = len(table)
    uid = ''.join(map(lambda x: table[random.randrange(table_size)],
                  range(size)))
    return uid


def byPrice(book_side, i_depth):
    '''
    Return the nth top prices of the order book side passed

    :param side_obj: Book Side object.
    '''
    i_depth2 = max(i_depth, 7)
    book_aux = book_side.this_side
    l_rtn = book_aux.get_n_top_prices(i_depth2, b_return_dataframe=False)
    f_price_to_filer = book_aux.other_side.best_queue[0]
    if not f_price_to_filer:
        return [QueueInfo(0, None)]
    if book_aux.s_side == 'BID':
        l_rtn1 = [QueueInfo(x[1].i_qty, x[0]) for x in l_rtn
                  if x[0] < f_price_to_filer]
    else:
        l_rtn1 = [QueueInfo(x[1].i_qty, x[0]) for x in l_rtn
                  if x[0] > f_price_to_filer]
    if len(l_rtn1) == 0:
        if len(l_rtn) == 0:
            return [QueueInfo(0, None)]
        x = l_rtn[-1]
        return [QueueInfo(x[1].i_qty, x[0])]
    return l_rtn1[:i_depth]


class Side(Enum):
    BID = 1
    ASK = 2

    def __eq__(self, o):
        if isinstance(o, Side):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.value.__hash__()


class Source(Enum):
    IDLE = 0
    MARKET = 1
    ORDER = 2
    COMMAND = 3

    def __eq__(self, o):
        if isinstance(o, Source):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class UpdateReason(Enum):
    BID_SIDE = 0
    ASK_SIDE = 1
    TRADES = 2
    EMPTY_BAR = 3

    def __eq__(self, o):
        if isinstance(o, UpdateReason):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class TimeInForce(Enum):
    DAY = 0
    FAK = 3
    FOK = 4

    def __eq__(self, o):
        if isinstance(o, TimeInForce):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class FIXStatus(Enum):
    IDLE = 0
    PENDING = 1
    NEW = 2
    PARTIALLY_FILLED = 3
    FILLED = 4
    CANCELLED = 5
    REPLACED = 6
    REJECTED = 8

    def __eq__(self, o):
        if isinstance(o, FIXStatus):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class QuitReason(Enum):
    USER_QUIT = 0
    NEUTRINO_QUIT = 1
    SYSTEM_QUIT = 2
    ALGOMAN_QUIT = 3
    OUT_OF_SYNC_QUIT = 4

    def __eq__(self, o):
        if isinstance(o, QuitReason):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


# class CandleInterval(Enum):
#     ONE_MINUTE = 60
#     FIVE_MINUTES = 60 * 5
#     ONE_HOUR = 60 * 60
#     ONE_DAY = 60 * 60 * 24

#     def __eq__(self, o):
#         if isinstance(o, CandleInterval):
#             return o.value == self.value
#         elif isinstance(o, int):
#             return o == self.value
#         return False

#     def __str__(self):
#         return self.name


class IndicatorSource(Enum):
    OPEN = 'open'
    HIGH = 'pmax'
    LOW = 'pmin'
    CLOSE = 'close'
    VOLUME = 'volume'
    QUANTITY = 'quantity'
    QUANTITY_BUY = 'quantity_buy'
    QUANTITY_SELL = 'quantity_sell'
    QUANTITY_ACCUMULATED = 'quantity_accumulated'
    QUANTITY_SELL_ACCUMULATED = 'quantity_sell_accumulated'
    QUANTITY_BUY_ACCUMULATED = 'quantity_buy_accumulated'

    def __eq__(self, o):
        if isinstance(o, IndicatorSource):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class NotificationEvent(Enum):
    POPUP = 0

    def __eq__(self, o):
        if isinstance(o, TimeInForce):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class OrderType(Enum):
    NONE = 0
    LIMIT = 1
    MARKET = 2
    STOP = 3
    STOP_LIMIT = 4

    def __eq__(self, o):
        if isinstance(o, OrderType):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class OrderStatus(Enum):
    WAIT = 0
    WAIT_REPLACE = 1
    WAIT_CANCEL = 2
    ACTIVE = 3
    REPLACED = 4
    PARTIAL_FILLED = 5
    FILLED = 6
    CANCELLED = 7
    REJECTED = 8

    def __eq__(self, o):
        if isinstance(o, OrderStatus):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()

    def __or__(self, o):
        if isinstance(o, OrderStatus):
            return self.value | o.value
        elif isinstance(o, int):
            return self.value | o

    def __ror__(self, o):
        if isinstance(o, OrderStatus):
            return self.value | o.value
        elif isinstance(o, int):
            return self.value | o


class OrderRetCode(Enum):
    OK = 0
    ORDER_NOT_FOUND = -1
    RISK_INVALID_NET = -2
    INVALID_QUANTITY = -3
    INFLIGHT = -4

    def __eq__(self, o):
        if isinstance(o, OrderRetCode):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class IndicatorAverage(Enum):
    SMA = 0
    EMA = 1
    WMA = 2

    def __eq__(self, o):
        if isinstance(o, IndicatorAverage):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


class IndicatorName(Enum):
    NONE = 0
    SMA = 1
    EMA = 2
    MOM = 3
    SAMOM = 4
    TRANGE = 5
    SATR = 6
    ATR = 7
    SAADX = 8
    ADX = 9
    PLUS_DI = 10
    MINUS_DI = 11
    BBANDS = 12
    SABBANDS = 13
    STDDEV = 14
    RSI = 15
    SAR = 16
    OBV = 17
    STOCH = 18
    STOCHF = 19
    MACD = 20

    def __eq__(self, o):
        if isinstance(o, IndicatorName):
            return o.value == self.value
        elif isinstance(o, int):
            return o == self.value
        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        '''
        Allow the Order object be used as a key in a hash table. It is used by
        dictionaries
        '''
        return self.value.__hash__()


s_book_info = 'price quantity detail orderID order_id virtual_md_id'
s_trade_info = 'price quantity buyer seller date time status tradeID, trade_id'
s_trade_info += ', datetime'

QueueInfo = namedtuple('QueueInfo', 'quantity price')
NextInfo = namedtuple('NextInfo', 'qty timeInForce price side userData')
BookData = namedtuple('BookData', s_book_info)
TradeInfo = namedtuple('TradeInfo', s_trade_info)
SecurityInfo = namedtuple('SecurityInfo', 'priceIncrement minOrderQty')

StatusEntry = namedtuple('StatusEntry', 'status open_trade_time')
TunnelEntry = namedtuple('StatusEntry', 'low_price high_price')


class Transaction(object):
    '''
    '''
    def __init__(self):
        self.order = None
        self.price = 0.0
        self.qty = 0
        self.cumQty = 0
        self.timeInForce = TimeInForce.DAY
        self.side = Side.BID
        self.status = FIXStatus.IDLE
        self.clOrdID = gen_uuid()
        self.secondaryOrderID = ''
        self.userData = ''
        self.neutrinogymData = {}
        self.isPending = False
        self.isAlive = False
        self._last_price = 0.0
        self._last_qty = 0
        self._last_quantity = 0

    @staticmethod
    def build1(order):
        t = Transaction()
        t.order = order
        t.price = None
        t.qty = None
        t.cumQty = 0
        t.timeInForce = TimeInForce.DAY
        t.side = Side.BID
        t.status = FIXStatus.IDLE
        t.clOrdID = 'clOrdID:987654321'
        t.secondaryOrderID = 'secondaryOrderID:asdfasdf'
        t.userData = {'userdata': 'asdfqwer'}
        t.neutrinogymData = {}
        t.isPending = False
        t.isAlive = False
        return t


class Summary(object):
    bidCount = None
    askCount = None
    tradeCount = None
    statusChanged = None
    # new fields, not valid to production
    tradeCountIncrement = 0
    newBidOrders = 0
    canceledBidOrders = 0
    replacedOBidrders = 0
    newAskOrders = 0
    canceledAskOrders = 0
    replacedOAskrders = 0


class Update(object):
    symbol = None
    reason = []
    times = []
    bid_count = None
    ask_count = None
    trade_count = None
    status_changed = None


class SchaduleInfos(object):
    # NOTE: valid to simulation only
    name = ''
    kind = ''
    _scheduled_obj = None
    every = 10**6
    at = 21*60**2
    _last_time = 0

    def __init__(self, name):
        self.name = name

    def should_trigger(self, f_time):
        if self.kind == 'at':
            if f_time > self.at:
                self._last_time = f_time
                return True
        else:
            if f_time > self._last_time + self.every:
                self._last_time = f_time
                return True
        return False

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __ne__(self, other):
        if isinstance(other, str):
            return self.name != other
        return not self.__eq__(other)

    def __hash__(self):
        return self.name.__hash__()

    def __str__(self):
        return self.name


class Client(object):
    '''
    '''
    def __init__(self):
        pass


class Order(object):
    '''
    Order class is a representation of an area in memory that is used to send
    orders to market. This memory address can be reused across multiple orders,
    which is the preferred way of working. Do not dispose of these objects, as
    they are used internally by Neutrino to be updated upon messages arriving
    from the network.
    '''
    def __init__(self, side):
        self.side = side
        self.status = FIXStatus.IDLE
        self.current = Transaction.build1(self)
        self.client = None
        self.symbol = '<undef>'
        self.orderID = '<undef>'
        self.leg_order = -1
        self.next = Transaction.build1(self)
        self.userData = '<undef>'

    def isPending(self):
        b_t1 = self.status == FIXStatus.PENDING
        b_t2 = self.current and self.current.status == FIXStatus.PENDING
        return b_t1 or b_t2

    def isAlive(self):
        '''
        :return: True if order status held by the memory is one of: PENDING,
        NEW, REPLACED, PARTIALLY_FILLED.
        Otherwise, False.
        '''
        l_is_alive = [FIXStatus.PENDING, FIXStatus.NEW, FIXStatus.REPLACED,
                      FIXStatus.PARTIALLY_FILLED]
        b_t1 = self.status in l_is_alive
        b_t2 = self.current and self.current.status in l_is_alive
        return b_t1 or b_t2

    def _isDead(self):
        '''
        :return: True if order status held by the memory is one of: PENDING,
        NEW, REPLACED, PARTIALLY_FILLED.
        Otherwise, False.
        '''

        l_is_dead = [FIXStatus.FILLED, FIXStatus.CANCELLED, FIXStatus.REJECTED]
        b_t1 = self.status in l_is_dead
        b_t2 = self.current and self.current.status in l_is_dead
        return b_t1 or b_t2

    def __str__(self):
        '''
        '''
        s_rtn = 'Order(Symbol={}, Side={}, Status={}({}), '
        s_rtn += 'Price={}, Qty={}, ID={})'
        return s_rtn.format(
            self.symbol, self.side, self.current.status, self.status,
            self.current.price, self.current.qty, self.userData['id'])

    def __repr__(self):
        '''
        '''
        return self.__str__()


class InstrumentRegister(object):
    '''
    '''
    def __init__(self, s_instrument, b_ready=True):
        '''
        '''
        self._s_instr = s_instrument
        self.b_ready = b_ready

    @property
    def book(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return None
        return ENV.get_order_book(self._s_instr, False)

    @property
    def trades(self):
        '''
        Access the trades of the instrument, if it is available
        '''
        if not self.b_ready:
            return None
        return ENV.get_last_trades_new(self.book)

    def ready(self):
        return self.b_ready

    @property
    def name(self):
        '''
        :return: Symbol name for this book.
        '''
        return self.book.name

    @property
    def price_increment(self):
        return self.book.security().priceIncrement

    @property
    def min_order_qty(self):
        return self.book.security().minOrderQty


class CandleSelector(object):
    '''
    '''
    def __init__(self, bar_data, i_corrector=0):
        self.bar_data = bar_data
        self.this_iter = iter(self.bar_data.l)
        self.i_corrector = i_corrector
        self.n = 0

    def __iter__(self):
        self.n = 0
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.n < len(self):
            o = self.bar_data.l[self.n]
            self.n += 1
            return o
        self.n = 0
        raise StopIteration
        # return next(self.this_iter)

    def __len__(self):
        return len(self.bar_data.l)

    def __getitem__(self, key):
        return self.bar_data.l[int(key+self.i_corrector)]


class BandsRegister(object):
    '''
    '''
    def __init__(self, bar_obj, s_alias, i_inner_idx=0):
        self.bar_obj = bar_obj
        self._s_alias = s_alias
        self.i_inner_idx = i_inner_idx
        self.s_name = bar_obj._bar_obj._alias.get(s_alias, None)
        self.properties = IndicatorProperties()
        self._removed = False
        self.values = [
            IndicatorSelector(self, 0),
            IndicatorSelector(self, 1),
            IndicatorSelector(self, 2)]

    def remove_indicator(self):
        self._removed = True
        ENV.candles.reset(
            this_candle=self.bar_obj._bar_obj,
            this_conf=self._s_alias)

    @property
    def data(self):
        if self._removed:
            raise NoneObjectError
        # return self.bar_obj._bar_obj.d_candle_data[self.s_name]['data']
        if not self.bar_obj.b_ready:
            return []
        return self.bar_obj._bar_data[self.s_name]

    @property
    def last_id(self):
        if self._removed:
            raise NoneObjectError
        if not self.bar_obj.b_ready:
            return 0
        i_len = len(self.values[0])
        if i_len == 0:
            return 0
        return (self.bar_obj._bar_data['LST'].count - 1)


class IndicatorRegister(object):
    '''
    '''
    def __init__(self, bar_obj, s_alias, i_inner_idx=0):
        self.bar_obj = bar_obj
        self._s_alias = s_alias
        self.i_inner_idx = i_inner_idx
        self.s_name = bar_obj._bar_obj._alias.get(s_alias, None)
        self.properties = IndicatorProperties()
        self._removed = False

        self._conf = dict(zip(
            ['what', 'symbol', 'conf'], self.s_name.split(':')))

        # self.values = IndicatorSelector(self, i_inner_idx)
        self.values = [IndicatorSelector(self, 0)]

    def remove_indicator(self):
        # NOTE: it is not working properly
        self._removed = True
        ENV.candles.reset(
            this_candle=self.bar_obj._bar_obj,
            this_conf=self._s_alias)  # self._conf)

    @property
    def data(self):
        if self._removed:
            raise NoneObjectError
        # return self.bar_obj._bar_obj.d_candle_data[self.s_name]['data']
        if not self.bar_obj.b_ready:
            return []
        return self.bar_obj._bar_data[self.s_name]

    @property
    def last_id(self):
        if self._removed:
            raise NoneObjectError
        if not self.bar_obj.b_ready:
            return 0
        i_len = len(self.values[0])
        if i_len == 0:
            return 0
        return (self.bar_obj._bar_data['LST'].count - 1)


class IndicatorSelector(object):
    '''
    '''
    def __init__(self, bar_data, i_inner_idx=0):
        self.bar_data = bar_data
        self.i_inner_idx = i_inner_idx
        self.n = 0

    def __iter__(self):
        self.n = 0
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.n < len(self.bar_data.data):
            obj = self.bar_data.data[self.i_inner_idx][self.n]
            self.n += 1
            return obj
        self.n = 0
        raise StopIteration

    def __len__(self):
        if isinstance(self.bar_data.data, type(None)):
            return 0
        return len(self.bar_data.data)

    def __getitem__(self, key):
        if isinstance(self.bar_data.data, type(None)):
            return np.nan
        try:
            obj = self.bar_data.data[self.i_inner_idx][int(key)]
            return obj
        # TODO: I dont know wtf
        except IndexError:
            return np.nan


class IndicatorProperties(object):
    bar_count = 10
    source = IndicatorSource.CLOSE
    sa_bar_count = 10
    deviation_count = 1
    sa_bar_count = 10
    deviation_up = 1
    deviation_down = 1
    average = IndicatorAverage.SMA


class BarProperties(object):
    bar_count = None
    interval = None
    symbol = None


class Symbol(object):
    def __init__(self, l_instrument):
        self.instruments = iter(l_instrument)
        self._len = len(l_instrument)
        self.n = 0
        self.l_instruments = l_instrument

    def __iter__(self):
        self.n = 0
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.n < self._len:
            s = self.l_instruments[self.n]
            self.n += 1
            return s
        self.n = 0
        raise StopIteration

    def __getitem__(self, key):
        return self.l_instruments[key]


class CandleRegister(object):
    '''
    '''
    def __init__(self, candle_data, b_ready=True):
        '''
        '''
        self._bar_obj = candle_data
        self._indicator_data = {}
        self._bar_data = {}
        self._selectors = {}
        self.b_ready = b_ready
        self.properties = BarProperties()
        self.properties.symbol = None
        self.properties.interval = None
        self.properties.bar_count = None

    def add_sma(self, bar_count, source):
        '''

        bar_count: integer.
        source: IndicatorSource object.
        '''
        self.b_ready = False
        if 'SMA' not in self._indicator_data:
            self._indicator_data['SMA'] = {}
        s_alias = 'SMA_%i_%s' % (bar_count, source)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='SMA',
            s_input=source.value,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['SMA'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.SMA
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.source = source
        return obj_rtn

    def add_satr(self, sa_bar_count):
        '''

        sa_bar_count: integer.
        '''
        self.b_ready = False
        if 'SATR' not in self._indicator_data:
            self._indicator_data['SATR'] = {}
        s_alias = 'SATR_%i' % (sa_bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='SATR',
            i_time_period=sa_bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['SATR'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.SATR
        obj_rtn.properties.sa_bar_count = sa_bar_count
        return obj_rtn

    def add_adx(self, bar_count):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'ADX' not in self._indicator_data:
            self._indicator_data['ADX'] = {}
        s_alias = 'ADX_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='ADX',
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['ADX'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.ADX
        obj_rtn.properties.bar_count = bar_count
        return obj_rtn

    def add_mom(self, bar_count, source):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'MOM' not in self._indicator_data:
            self._indicator_data['MOM'] = {}
        s_alias = 'MOM_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='MOM',
            s_input=source.value,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['MOM'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.MOM
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.source = source
        return obj_rtn

    def add_samom(self, bar_count, sa_bar_count, source):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'SAMOM' not in self._indicator_data:
            self._indicator_data['SAMOM'] = {}
        s_alias = 'SAMOM_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='SAMOM',
            s_input=source.value,
            sa_period=sa_bar_count,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['SAMOM'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.SAMOM
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.sa_bar_count = sa_bar_count
        obj_rtn.properties.source = source
        return obj_rtn

    def add_stddev(self, bar_count, deviation_count, source):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'STDDEV' not in self._indicator_data:
            self._indicator_data['STDDEV'] = {}
        s_alias = 'STDDEV_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='STDDEV',
            nbdev=deviation_count,
            s_input=source.value,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['STDDEV'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.STDDEV
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.deviation_count = deviation_count
        obj_rtn.properties.source = source
        return obj_rtn

    def add_saadx(self, bar_count, sa_bar_count):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'SAADX' not in self._indicator_data:
            self._indicator_data['SAADX'] = {}
        s_alias = 'SAADX_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='SAADX',
            sa_period=sa_bar_count,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['SAADX'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.SAADX
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.sa_bar_count = sa_bar_count
        return obj_rtn

    def add_trange(self, bar_count=0):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'TRANGE' not in self._indicator_data:
            self._indicator_data['TRANGE'] = {}
        s_alias = 'TRANGE_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='TRANGE',
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['TRANGE'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.TRANGE
        return obj_rtn

    def add_minus_di(self, bar_count):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'MINUS_DI' not in self._indicator_data:
            self._indicator_data['MINUS_DI'] = {}
        s_alias = 'MINUS_DI_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='MINUS_DI',
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        self._indicator_data['MINUS_DI'][s_alias] = obj_rtn
        obj_rtn.name = IndicatorName.MINUS_DI
        obj_rtn.properties.bar_count = bar_count
        return obj_rtn

    def add_plus_di(self, bar_count):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'PLUS_DI' not in self._indicator_data:
            self._indicator_data['PLUS_DI'] = {}
        s_alias = 'PLUS_DI_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='PLUS_DI',
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        obj_rtn.name = IndicatorName.PLUS_DI
        obj_rtn.properties.bar_count = bar_count
        self._indicator_data['PLUS_DI'][s_alias] = obj_rtn
        return obj_rtn

    def add_atr(self, bar_count):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'ATR' not in self._indicator_data:
            self._indicator_data['ATR'] = {}
        s_alias = 'ATR_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='ATR',
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        obj_rtn.name = IndicatorName.ATR
        obj_rtn.properties.bar_count = bar_count
        self._indicator_data['ATR'][s_alias] = obj_rtn
        return obj_rtn

    def add_ema(self, bar_count, source):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'EMA' not in self._indicator_data:
            self._indicator_data['EMA'] = {}
        s_alias = 'EMA_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='EMA',
            s_input=source.value,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        obj_rtn.name = IndicatorName.EMA
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.source = source
        self._indicator_data['EMA'][s_alias] = obj_rtn
        return obj_rtn

    def add_bbands(self, bar_count, deviation_up, deviation_down, average):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'BBANDS' not in self._indicator_data:
            self._indicator_data['BBANDS'] = {}
        s_alias = 'BBANDS_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='BBANDS',
            i_time_period=bar_count,
            nbdevup=deviation_up,
            nbdevdn=deviation_down,
            matype=average.value)
        obj_rtn = BandsRegister(self, s_alias)
        obj_rtn.name = IndicatorName.BBANDS
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.deviation_up = deviation_up
        obj_rtn.properties.deviation_down = deviation_down
        obj_rtn.properties.average = average
        self._indicator_data['BBANDS'][s_alias] = obj_rtn
        return obj_rtn

    def add_sabbands(
            self, bar_count, deviation_up, deviation_down, sa_bar_count,
            average):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'SABBANDS' not in self._indicator_data:
            self._indicator_data['SABBANDS'] = {}
        s_alias = 'SABBANDS_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='SABBANDS',
            i_time_period=bar_count,
            nbdevup=deviation_up,
            nbdevdn=deviation_down,
            sa_period=sa_bar_count,
            matype=average.value)
        obj_rtn = BandsRegister(self, s_alias)
        obj_rtn.name = IndicatorName.SABBANDS
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.deviation_up = deviation_up
        obj_rtn.properties.deviation_down = deviation_down
        obj_rtn.properties.average = average
        obj_rtn.properties.sa_bar_count = sa_bar_count
        self._indicator_data['SABBANDS'][s_alias] = obj_rtn
        return obj_rtn

    def add_rsi(self, bar_count, source):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        if 'RSI' not in self._indicator_data:
            self._indicator_data['RSI'] = {}
        s_alias = 'RSI_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='RSI',
            s_input=source.value,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        obj_rtn.name = IndicatorName.RSI
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.source = source
        self._indicator_data['RSI'][s_alias] = obj_rtn
        return obj_rtn

    def add_sar(self, acceleration, maximum):
        '''

        acceleration: integer.
        maximum: integer.
        '''
        self.b_ready = False
        bar_count = 0. # not used in this Indicator
        if 'SAR' not in self._indicator_data:
            self._indicator_data['SAR'] = {}
        s_alias = 'SAR_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='SAR',
            acceleration=acceleration,
            maximum=maximum,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        obj_rtn.name = IndicatorName.SAR
        obj_rtn.properties.acceleration = acceleration
        obj_rtn.properties.maximum = maximum
        obj_rtn.properties.bar_count = bar_count
        self._indicator_data['SAR'][s_alias] = obj_rtn
        return obj_rtn

    def add_obv(self, source):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        bar_count = 0. # not used in this Indicator
        if 'OBV' not in self._indicator_data:
            self._indicator_data['OBV'] = {}
        s_alias = 'OBV_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='OBV',
            s_input=source.value,
            i_time_period=bar_count)
        obj_rtn = IndicatorRegister(self, s_alias)
        obj_rtn.name = IndicatorName.OBV
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.source = source
        self._indicator_data['OBV'][s_alias] = obj_rtn
        return obj_rtn

    def add_stoch(self, fast_k_ma_period, slow_k_ma_period,
                  slow_k_ma_type, slow_d_ma_period, slow_d_ma_type):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        bar_count = 0. # not used in this Indicator
        if 'STOCH' not in self._indicator_data:
            self._indicator_data['STOCH'] = {}
        s_alias = 'STOCH_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='STOCH',
            i_time_period=bar_count,
            fast_k_ma_period=fast_k_ma_period,
            # fast_ma_type=fast_ma_type.value,
            slow_k_ma_period=slow_k_ma_period,
            slow_k_ma_type=slow_k_ma_type.value,
            slow_d_ma_period=slow_d_ma_period,
            slow_d_ma_type=slow_d_ma_type.value)
        obj_rtn = BandsRegister(self, s_alias)
        obj_rtn.name = IndicatorName.STOCH
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.fast_k_ma_period = fast_k_ma_period
        # obj_rtn.properties.fast_ma_type = fast_ma_type
        obj_rtn.properties.slow_k_ma_period = slow_k_ma_period
        obj_rtn.properties.slow_k_ma_type = slow_k_ma_type
        obj_rtn.properties.slow_d_ma_period = slow_d_ma_period
        obj_rtn.properties.slow_d_ma_type = slow_d_ma_type

        self._indicator_data['STOCH'][s_alias] = obj_rtn
        return obj_rtn

    def add_stochf(self, fast_k_ma_period, fast_d_ma_period, fast_d_ma_type):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        bar_count = 0. # not used in this Indicator
        if 'STOCHF' not in self._indicator_data:
            self._indicator_data['STOCHF'] = {}
        s_alias = 'STOCHF_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='STOCHF',
            i_time_period=bar_count,
            fast_k_ma_period=fast_k_ma_period,
            fast_d_ma_period=fast_d_ma_period,
            fast_d_ma_type=fast_d_ma_type.value)
        obj_rtn = BandsRegister(self, s_alias)
        obj_rtn.name = IndicatorName.STOCHF
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.fast_k_ma_period = fast_k_ma_period
        obj_rtn.properties.fast_d_ma_period = fast_d_ma_period
        obj_rtn.properties.fast_d_ma_type = fast_d_ma_type

        self._indicator_data['STOCHF'][s_alias] = obj_rtn
        return obj_rtn

    def add_macd(self, fast_ma_type, fast_ma_period, slow_ma_type,
        slow_ma_period, signal_ma_type, signal_ma_period):
        '''

        bar_count: integer.
        '''
        self.b_ready = False
        bar_count = 0. # not used in this Indicator
        if 'MACD' not in self._indicator_data:
            self._indicator_data['MACD'] = {}
        s_alias = 'MACD_%i' % (bar_count)
        ENV.candles.add_indicator_to(
            this_candle=self._bar_obj,
            s_alias=s_alias,
            s_ta_name='MACD',
            i_time_period=bar_count,
            fast_ma_period=fast_ma_period,
            fast_ma_type=fast_ma_type.value,
            slow_ma_period=slow_ma_period,
            slow_ma_type=slow_ma_type.value,
            signal_ma_period=signal_ma_period,
            signal_ma_type=signal_ma_type.value)
        obj_rtn = BandsRegister(self, s_alias)
        obj_rtn.name = IndicatorName.MACD
        obj_rtn.properties.bar_count = bar_count
        obj_rtn.properties.fast_ma_period = fast_ma_period
        obj_rtn.properties.fast_ma_type = fast_ma_type
        obj_rtn.properties.slow_ma_type = slow_ma_type
        obj_rtn.properties.slow_ma_period = slow_ma_period
        obj_rtn.properties.signal_ma_type = signal_ma_type
        obj_rtn.properties.signal_ma_period = signal_ma_period

        self._indicator_data['MACD'][s_alias] = obj_rtn
        return obj_rtn


    @property
    def last_id(self):
        '''
        Access the trades of the instrument, if it is available
        '''
        if not self.b_ready:
            return 0
        return (self._bar_data['LST'].count - 1)

    @property
    def open(self):
        '''
        Access the trades of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'open' not in self._selectors:
            self._selectors['open'] = CandleSelector(self._bar_data['LST'], -1)
        return self._selectors['open']

    @property
    def high(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'high' not in self._selectors:
            self._selectors['high'] = CandleSelector(self._bar_data['MAX'])
        return self._selectors['high']

    @property
    def low(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'low' not in self._selectors:
            self._selectors['low'] = CandleSelector(self._bar_data['MIN'])
        return self._selectors['low']

    @property
    def close(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'close' not in self._selectors:
            self._selectors['close'] = CandleSelector(self._bar_data['LST'])
        return self._selectors['close']

    @property
    def num_trades(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'num_trades' not in self._selectors:
            self._selectors['num_trades'] = CandleSelector(
                self._bar_data['NTRADES'])
        return self._selectors['num_trades']

    @property
    def quantity(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'quantity' not in self._selectors:
            self._selectors['quantity'] = CandleSelector(self._bar_data['QTD'])
        return self._selectors['quantity']

    @property
    def quantity_buy(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'quantity_buy' not in self._selectors:
            self._selectors['quantity_buy'] = CandleSelector(
                self._bar_data['QTD_B'])
        return self._selectors['quantity_buy']

    @property
    def quantity_sell(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'quantity_sell' not in self._selectors:
            self._selectors['quantity_sell'] = CandleSelector(
                self._bar_data['QTD_S'])
        return self._selectors['quantity_sell']

    @property
    def quantity_accumulated(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'quantity_accumulated' not in self._selectors:
            self._selectors['quantity_accumulated'] = CandleSelector(
                self._bar_data['CUMQTD'])
        return self._selectors['quantity_accumulated']

    @property
    def quantity_buy_accumulated(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'quantity_buy_accumulated' not in self._selectors:
            self._selectors['quantity_buy_accumulated'] = CandleSelector(
                self._bar_data['CUMQTD_B'])
        return self._selectors['quantity_buy_accumulated']

    @property
    def quantity_sell_accumulated(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'quantity_sell_accumulated' not in self._selectors:
            self._selectors['quantity_sell_accumulated'] = CandleSelector(
                self._bar_data['CUMQTD_S'])
        return self._selectors['quantity_sell_accumulated']

    @property
    def volume(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'volume' not in self._selectors:
            self._selectors['volume'] = CandleSelector(
                self._bar_data['VOLUME'])
        return self._selectors['volume']

    @property
    def timestamps(self):
        '''
        Access the book of the instrument, if it is available
        '''
        if not self.b_ready:
            return []
        if 'timestamps' not in self._selectors:
            self._selectors['timestamps'] = CandleSelector(
                self._bar_data['TS'])
        return self._selectors['timestamps']

    def remove_indicator(self, indicator):
        '''

        :param indicator: Indicator|BandsResgister object
        '''
        # NOTE: it is not working properly. It used unsubscribe but the data
        #    persists
        indicator.remove_indicator()

    def get_indicators(self):
        l_rtn = []
        for s_key in self._indicator_data:
            l_aux = self._indicator_data[s_key].values()
            l_rtn += l_aux
        return l_rtn

    def ready(self):
        return self.b_ready


class Book(object):
    '''
    A book class contains all the offers for buy and sell present in a
    particular symbol.
    '''
    def __init__(self):
        self.bookAsk = []
        self.bookBid = []
        self.s_name = '<Book.name undefined>'

    def bid(self):
        '''
        Exposes the sides of a book.

        :return: An instance of class Side with a list of bid offers.
        '''
        return self.bookBid

    def ask(self):
        return self.bookAsk

    def name(self):
        '''
        :return: Symbol name for this book.
        '''
        return self.s_name

    def state(self):
        pass

    def sequence(self):
        pass

    def byprice(self):
        pass

    def __str__(self):
        s = '\nASK -----------\n'
        for ask in self.bookAsk:
            s += str(ask) + '\n'
        s = 'BID -------------\n'
        for bid in self.bookBid:
            s += str(bid) + '\n'
        s += '-----------------\n'
        return s


class oms_client(object):

    _ready = False
    _id_mapping = {}

    @staticmethod
    def send_limit_order(
            symbol, side, price, quantity, time_in_force, i_id=11):
        '''
        Send a limit order

        symbol: string.
        side: neutrino.Side.
        price: float.
        quantity: int.
        time_in_force: neutrino.TimeInForce.
        '''
        orders = ENV.orders[i_id]
        instr = orders.get_instrument_from(s_symbol=symbol)
        # NOTE: tif in simulation is always the same
        # s_tif = orders._tif2str[time_in_force]
        i_order_id = orders.new_order(
            instr=instr, s_side=str(side), f_price=price, i_qty=quantity)
        if i_id not in oms_client._id_mapping:
            oms_client._id_mapping[i_id] = {}
        oms_client._id_mapping[i_id][i_order_id] = symbol
        return i_order_id

    @staticmethod
    def replace_limit_order(
            order, price, quantity, time_in_force, i_id=11):
        orders = ENV.orders[i_id]
        # NOTE: tif in simulation is always the same
        # s_tif = orders._tif2str[time_in_force]
        i_order_id = orders.modify_order(
            order=order.order, f_price=price, i_qty=quantity, s_tif='day')
        oms_client._id_mapping[i_id][i_order_id] = order.symbol
        return i_order_id

    @staticmethod
    def get_order_by_id(order_id, i_id=11):
        '''
        '''
        orders = ENV.orders[i_id]
        if i_id not in oms_client._id_mapping:
            return None
        symbol = oms_client._id_mapping[i_id].get(order_id, None)
        if not symbol:
            return None
        instr = orders.get_instrument_from(s_symbol=symbol)
        order = instr.get_my_order_by_id(order_id)
        if not order_id or not order:
            return None
        return LimitOrderEntry(order, i_id=i_id)

    @staticmethod
    def get_total_quantity(symbol, side, status_combination=None, i_id=11):
        '''
        '''
        orders = ENV.orders[i_id]
        instr = orders.get_instrument_from(s_symbol=symbol)
        return instr.get_active_qty(str(side))

    @staticmethod
    def get_live_orders(symbol, side=None, price=None, i_id=11):
        '''
        '''
        orders = ENV.orders[i_id]
        s_tests = ''.join(
            [str((not isinstance(x, type(None)))*1) for x in [side, price]])
        instr = orders.get_instrument_from(s_symbol=symbol)
        if s_tests == '10':
            l_rtn = instr.get_my_orders_by_side(str(side))
        elif s_tests == '01':
            l_bids = instr.get_my_orders_by_price('BID', price)
            l_asks = instr.get_my_orders_by_price('ASK', price)
            l_rtn = list(l_bids) + list(l_asks)
        elif s_tests == '11':
            l_rtn = instr.get_my_orders_by_price(str(side), price)
        elif s_tests == '00':
            l_bids = instr.get_my_orders_by_side('BID')
            l_asks = instr.get_my_orders_by_side('ASK')
            l_rtn = list(l_bids) + list(l_asks)
        l_rtn = [oms_client.get_order_by_id(x) for x in l_rtn]

        return l_rtn

    @staticmethod
    def get_all_orders(symbol, side=None, price=None, i_id=11):
        '''
        '''
        # NOTE: currently there is not option to get a list of older orders
        return oms_client.get_live_orders(
            symbol, side=side, price=price, i_id=i_id)

    @staticmethod
    def cancel(order_entry):
        '''
        '''
        return order_entry.cancel()

    @staticmethod
    def cancel_all(symbol=None, side=None, price=None, i_id=11):
        '''
        '''
        orders = ENV.orders[i_id]
        s_tests = ''.join(
            [str((not isinstance(x, type(None)))*1)
             for x in [symbol, side, price]])
        instr = None
        if s_tests[0] == '1':
            instr = orders.get_instrument_from(s_symbol=symbol)
        if s_tests == '000':
            orders.cancel_all_orders()
        elif s_tests == '100':
            orders.cancel_instrument_orders(instr)
        elif s_tests == '110':
            orders.cancel_orders_by_side(instr, s_side=str(side))
        # elif s_tests == '111':
        #     orders.cancel_orders_by_price(instr, s_side=side, f_price=price)
        elif s_tests == '101':
            orders.cancel_orders_by_price(instr, s_side='BID', f_price=price)
            orders.cancel_orders_by_price(instr, s_side='ASK', f_price=price)


class LimitOrderEntry(object):

    _status_mapping = {
        FIXStatus.IDLE: OrderStatus.WAIT,
        FIXStatus.PENDING: OrderStatus.WAIT,
        FIXStatus.NEW: OrderStatus.ACTIVE,
        FIXStatus.PARTIALLY_FILLED: OrderStatus.PARTIAL_FILLED,
        FIXStatus.FILLED: OrderStatus.FILLED,
        FIXStatus.CANCELLED: OrderStatus.CANCELLED,
        FIXStatus.REPLACED: OrderStatus.REPLACED,
        FIXStatus.REJECTED: OrderStatus.REJECTED}

    def __init__(self, order, i_id):
        self.order = order
        self.i_id = i_id
        self.unique_id = order.userData['new_id']
        self.side = order.side
        self.type = OrderType.LIMIT
        self.account = 9999
        self.symbol = order.symbol

        self._time_in_force = None
        self._secondary_order_id = None
        self._status = None
        self._price = None
        self._last_price = None
        self._trigger_price = None
        self._quantity = None
        self._last_quantity = 0
        self._filled_quantity = None
        self._leaves_quantity = None
        self._transact_time = None
        self._client_order_id = None
        self._original_client_order_id = None

    @property
    def secondary_order_id(self):
        if self.order.current and self.order.current.secondaryOrderID:
            return int(self.order.current.secondaryOrderID)
        return None

    @property
    def virtual_md_id(self):
        if self.order.current and self.order.current.secondaryOrderID:
            if self.order.current.secondaryOrderID[:3] != 'sec':
                return int(self.order.current.secondaryOrderID)
        return None

    @property
    def time_in_force(self):
        if self.order.current and self.order.current.timeInForce:
            return self.order.current.timeInForce
        return self.order.next.timeInForce

    @property
    def status(self):
        if self.order.current and self.order.current.status:
            return self._status_mapping[self.order.current.status]
        return self._status_mapping[self.order.next.status]

    @property
    def price(self):
        if not isinstance(self.order.current, type(None)):
            if not isinstance(self.order.current.price, type(None)):
                return self.order.current.price
        return self.order.next.price

    @property
    def last_price(self):
        if self.order.current:
            if not isinstance(self.order.current.price, type(None)):
                return self.order.current._last_price
        return 0.

    @property
    def quantity(self):
        if self.order.current:
            if not isinstance(self.order.current.qty, type(None)):
                return self.order.current.qty
        return self.order.next.qty

    @property
    def filled_quantity(self):
        if self.order.current:
            if not isinstance(self.order.current.qty, type(None)):
                return self.order.current.cumQty
        return 0

    @property
    def leaves_quantity(self):
        if self.order.current:
            if not isinstance(self.order.current.qty, type(None)):
                f_qty = self.order.current.qty - self.order.current.cumQty
                return f_qty
        return self.order.next.qty

    @property
    def transact_time(self):
        return 0

    @property
    def last_quantity(self):
        if self.order.current:
            if not isinstance(self.order.current.qty, type(None)):
                return self.order.current._last_quantity
        return 0

    def cancel(self):
        orders = ENV.orders[self.i_id]
        orders.cancel_order(self.order)
        return self.unique_id

    def replace(self, price, quantity, time_in_force):
        return self.replace_limit(price, quantity, time_in_force)

    def replace_limit(self, price, quantity, time_in_force):
        # DEPRECTED
        orders = ENV.orders[self.i_id]
        # NOTE: tif in simulation is always the same
        # s_tif = orders._tif2str[time_in_force]
        i_order_id = orders.modify_order(
            order=self.order, f_price=price, i_qty=quantity, s_tif='day')
        if not isinstance(i_order_id, type(None)):
            self.unique_id = i_order_id
        else:
            return -1
        return self.unique_id

    def is_alive(self):
        return self.order.isAlive()

    def is_pending(self):
        return self.order.isPending()

    def is_dead(self):
        return self.order._isDead()

    def __str__(self):
        return str(self.order)

    def __repr__(self):
        '''
        '''
        return self.__str__()


class SummaryLine(object):
    def __init__(self, instrumet):
        self._instr = instrumet

    @property
    def symbol(self):
        return self._instr.name

    @property
    def bid(self):
        return self._instr.book.bid[0]

    @property
    def ask(self):
        return self._instr.book.ask[0]

    @property
    def last_trade(self):
        return self._instr.trades[-1]

    @property
    def stats(self):
        raise NotImplementedError('Implement SummaryLine.stats')

    @property
    def status(self):
        return StatusEntry(self._instr.book.state, '')


class PositionData(object):
    def __init__(self, instrument, b_partial=False, b_init=False):
        self._instr = instrument
        self.b_partial = b_partial
        self.b_init = b_init

    @property
    def net(self):
        if self.b_init:
            i_pos = self.bid_quantity
            i_pos -= self.ask_quantity
            return i_pos
        return self._instr.get_position()

    @property
    def bid_quantity(self):
        if self.b_partial:
            f_pos = self.net
            if f_pos >= 0:
                return 0
            return abs(f_pos)
            # sum([p for q, p in self._instr._open_pos['BID']])
        i_pos = self._instr._init_pos['qBid']
        if not self.b_init:
            i_pos += self._instr._position['qBid']
        return i_pos

    @property
    def ask_quantity(self):
        if self.b_partial:
            f_pos = self.net
            if f_pos <= 0:
                return 0
            return abs(f_pos)
        i_pos = self._instr._init_pos['qAsk']
        if not self.b_init:
            i_pos += self._instr._position['qAsk']
        return i_pos

    @property
    def bid_volume(self):
        if self.b_partial:
            f_pos = self.net
            if f_pos <= 0:
                return 0
            return sum([p*q for q, p in self._instr._open_pos['BID']])
        f_vol = self._instr._init_pos['Bid']
        if not self.b_init:
            f_vol += self._instr._position['Bid']
        return f_vol

    @property
    def ask_volume(self):
        if self.b_partial:
            f_pos = self.net
            if f_pos >= 0:
                return 0
            return sum([p*q for q, p in self._instr._open_pos['ASK']])
        f_vol = self._instr._init_pos['Ask']
        if not self.b_init:
            f_vol += self._instr._position['Ask']
        return f_vol

    @property
    def net_price(self):
        f_pos = self.net
        f_netvol = self.ask_volume - self.bid_volume
        if not f_netvol:
            return 0.
        if not f_pos:
            return f_netvol
        return abs(f_netvol/f_pos)


class PositionStatus(object):
    def __init__(self, intrument):
        self.total = PositionData(intrument)
        self.partial = PositionData(intrument, b_partial=True)
        self.initial = PositionData(intrument, b_init=True)


class Position(object):

    @staticmethod
    def get(symbol, i_id=11):
        '''
        '''
        orders = ENV.orders[i_id]
        instr = orders.get_instrument_from(s_symbol=symbol)
        return PositionStatus(instr)

    def __call__(self, obj_agent):
        # self._current_agent_id = obj_agent._id2env
        return self


class Oms(object):
    '''
    Handle orders and keep all trasations related to them

    Methods to create and manupulate orders:
    - send_limit_order: TODO
    - replace_limit_order: TODO
    - cancel: TODO
    - cancel_all: TODO

    Methods to check orders already sent:
    - get_orders(<symbol>="", <side>=NONE_SIDE, <price>=-1)
    - get_live_orders(<symbol>="", <side>=NONE_SIDE, <price>=-1)
    - get_total_quantity(<symbol>, <side>, <tatus_combination>=0)
    - get_order_by_id(<unique_id>)

    TODO

    '''

    @staticmethod
    def send_limit_order(
            symbol, side, price, quantity, time_in_force, i_id=11):
        return oms_client.send_limit_order(
            symbol=symbol, side=side, price=price, quantity=quantity,
            time_in_force=time_in_force, i_id=i_id)

    @staticmethod
    def replace(order_entry, price, quantity, time_in_force, i_id=11):
        return oms_client.replace_limit_order(
            order=order_entry, price=price, quantity=quantity,
            time_in_force=time_in_force, i_id=i_id)

    @staticmethod
    def send(symbol, side, price, quantity, time_in_force, i_id=11):
        return oms_client.send_limit_order(
            symbol=symbol, side=side, price=price, quantity=quantity,
            time_in_force=time_in_force, i_id=i_id)

    @staticmethod
    def get_order_by_id(order_id, i_id=11):
        return oms_client.get_order_by_id(order_id=order_id, i_id=i_id)

    @staticmethod
    def get_total_quantity(symbol, side, status=None, i_id=11):
        # TODO: cover all cases
        # only wait orders combination
        if isinstance(status, int) and status < 4:
            return 0
        return oms_client.get_total_quantity(
            symbol=symbol, side=side, i_id=i_id)

    @staticmethod
    def get_live_orders(symbol, side=None, price=None, i_id=11):
        return oms_client.get_live_orders(
            symbol=symbol, side=side, price=price, i_id=i_id)

    @staticmethod
    def get_all_orders(symbol, side=None, price=None, i_id=11):
        return oms_client.get_all_orders(
            symbol=symbol, side=side, price=price, i_id=i_id)

    @staticmethod
    def cancel(order_entry):
        return oms_client.cancel(order_entry)

    @staticmethod
    def cancel_all(symbol=None, side=None, price=None, i_id=11):
        return oms_client.cancel_all(
            symbol=symbol, side=side, price=price, i_id=i_id)

    def __call__(self, obj_agent):
        # self._current_agent_id = obj_agent._id2env
        return self


class ScheduledFunction(object):

    def __init__(self, function, s_name, i_hour=0, i_minute=0, i_interval=0):
        self.function = function
        self._name = s_name
        self.hour = i_hour
        self.minute = i_minute
        self.interval = i_interval


class Utils(object):

    _this_path = None

    @staticmethod
    def every(callback, interval, i_id=11):
        l_callback =  str(callback).split(' ')
        s_name = '[{};{}]'.format(l_callback[2], interval)
        return fx.every(
            name=s_name, interval=interval, callback=callback, i_id=i_id)

    @staticmethod
    def at(callback, hour, minute, i_id=11):
        l_callback =  str(callback).split(' ')
        s_name = '[{};{};{}]'.format(l_callback[2], hour, minute)
        return fx.at(
            name=s_name, hour=hour, minute=minute, callback=callback, i_id=i_id)

    @staticmethod
    def remove_function(function, i_id=11):
        return fx.remove_schedule(name=function._name, i_id=i_id)

    @staticmethod
    def get_functions(i_id=11):
        return fx.get_schedules(i_id=i_id)

    @staticmethod
    def now(b_str=False, b_ts=False, b_old=False):
        return fx.now(b_str=b_str, b_ts=b_ts, b_old=b_old)

    @staticmethod
    def notify(s_msg):
        fx.notify(NotificationEvent.POPUP, s_msg)

    @staticmethod
    def quit(i_id=11):
        fx.quit(i_id=i_id)

    @staticmethod
    def by_price(side, depth):
        return byPrice(book_side=side, i_depth=depth)

    @staticmethod
    def path():
        return Utils._this_path

    def __call__(self, obj_agent):
        # self._current_agent_id = obj_agent._id2env
        return self


class Market(object):

    @staticmethod
    def add(symbol, trade_callback='default', book_callback='default',
            trade_buffer_size=64, i_id=11):
        return fx.add(
            symbol=symbol,
            trade_callback=trade_callback,
            book_callback=book_callback,
            trade_buffer_size=trade_buffer_size,
            i_id=i_id)

    @staticmethod
    def remove(symbol_propty, i_id=11):
        return fx.remove(symbol_propty=symbol_propty, i_id=i_id)

    @staticmethod
    def get(symbol, i_id=11):
        return fx.get(symbol=symbol, i_id=i_id)

    @staticmethod
    def add_bar(symbol, bar_count, interval, callback='default', i_id=11):
        return fx.add_bar(
            symbol=symbol, bar_count=bar_count, interval=interval,
            callback=callback, i_id=i_id)

    @staticmethod
    def get_bar(symbol, bar_count, interval):
        return fx.get_bar(
            symbol=symbol, bar_count=bar_count, interval=interval)

    @staticmethod
    def remove_bar(candle_propty):
        return fx.remove_bar(candle_propty=candle_propty)

    @staticmethod
    def add_summary(symbol, summary_callback='default', i_id=11):
        obj_aux = fx.add(
            symbol=symbol,
            trade_callback=summary_callback,
            book_callback=None,
            trade_buffer_size=64,
            i_id=i_id)

        return SummaryLine(obj_aux)

    @staticmethod
    def remove_summary(summary_propty, i_id=11):
        symbol_propty = summary_propty._instr
        return fx.remove(symbol_propty=symbol_propty, i_id=i_id)



    def __call__(self, obj_agent):
        # self._current_agent_id = obj_agent._id2env
        return self


class fx(object):

    legs = {}
    online = True
    config_file = 'twap.conf'
    now_val = 0
    pending_callbacks = {}
    symbols_callbacks = {}
    time_callbacks = {}
    initial_time = 0
    trade_callback_used = {}

    @staticmethod
    def now(b_str=False, b_ts=False, b_old=False):
        if b_ts:
            s_ts = ENV.order_matching.s_time[:23]
            if not s_ts:
                return 0
            fx_now = (datetime.datetime.strptime(s_ts, '%Y-%m-%d %H:%M:%S.%f'))
            fx_now = (fx_now-datetime.datetime(1970, 1, 1)).total_seconds()
            return fx_now
        if b_str:
            return ENV.order_matching.s_time
        if not fx.initial_time:
            s_ts = ENV.order_matching.s_time[:10]
            s_ts += ' 02:00:00.000'
            fx_now = (datetime.datetime.strptime(s_ts, '%Y-%m-%d %H:%M:%S.%f'))
            fx_now = (fx_now-datetime.datetime(1970, 1, 1)).total_seconds()
            fx.initial_time = fx_now

        if b_old:
            return ENV.order_matching.f_time
        return fx.initial_time + ENV.order_matching.f_time

    @staticmethod
    def broadcast(s_msg):
        if s_msg:
            print(s_msg)

    @staticmethod
    def notify(eventtype, s_msg):
        '''
        ...

        :param eventtype: NotificationEvent.
        :param s_msg: string.
        '''
        if s_msg:
            print(s_msg)

    @staticmethod
    def getConfigFile():
        return fx.config_file

    @staticmethod
    def configureOrder(symbol, leg_number, order, client=None):
        '''
        First step in the process of sending an order.
        It sets some fields before further processing.

        :param symbol:
        :param leg_number
        :param order:
        :param client: string. Used just in neutrinogym
        :return:
        '''
        order.symbol = symbol
        order.leg_number = leg_number
        if client:
            order.client = client

    # symbol, 0, 3000.0, 3500.0, 100, '%06.1f', '%03d'
    # const std::string &name, size32_t leg, double pxmin, double pxmax,
    # quant_t qmax, const char *px_mask, const char *qty_mask
    @staticmethod
    def setLeg(symbol, legid, pmin, pmax, qmax, px_mask, qty_mask):
        '''
        Called only once per process, the `setLeg` method is used to setup all
        the symbols that will be used in the subsequent calls. Typically
        `setLeg` is called at system startup retrieving its parameters from
        some configuration file. Internally the API will allocate a transaction
        manager for every leg that will be used to send actual order requests.
        Currently there is a maximum of three legs, and an exception will be
        thrown in if the leg index falls outside this range.

        :param symbol: String identifying the symbol this leg will manage.
        :param legid: Leg index for this symbol.
        :param pmin: Minimum price for this symbol. Order requests out of the
            range [pmin-pmax] will be rejected.
        :param pmax: Maximum price for this symbol.
        :param qmax: Max quantity for this symbol.
        :param px_mask: A printf style mask used to format the prices for this
            symbol when sending orders.
        :param qty_mask: A printf style mask used to format quantities for this
        symbol when sending orders.
        :return: None
        '''

        fx.legs[symbol] = {}
        fx.legs[symbol][legid] = {'pmin': pmin, 'pmax': pmax, 'qmax': qmax,
                                  'px_mask': px_mask, 'qty_mask': qty_mask}

    @staticmethod
    def attachToLeg(order, legs_ix):
        '''
        Before actually sending any order, one has to 'attach' it to a
        transaction. `attachToLeg` does just that. The API maintains an array
        of 'legs', every symbol has its own leg. For single-symbol algorithms,
        `leg_index` is always 0.

        :param order: Reference to an Order memory object
        :param legs_ix: leg index in the internal array. T
        :return: None
        '''
        fx.legs[legs_ix] = order

    def setLookup(self, symbol):
        pass

    @staticmethod
    def isOnline(bookname):
        return fx.online

    @staticmethod
    def quit(i_id=11):
        ENV.done = True
        this_agent = ENV.agents_actions[i_id].owner
        if hasattr(this_agent, 'agent'):
            this_agent = this_agent.agent
        if hasattr(this_agent, 'finalize'):
            this_agent.finalize(QuitReason.USER_QUIT)

    @staticmethod
    def cancel(order_mem):
        '''
        Delivers a cancel request

        :param order_mem: reference to a Order memory object.
        :return:
        '''
        ENV.agents_actions[order_mem.client].append_msg(('cancel', order_mem))
        return True

    @staticmethod
    def send(order_mem):
        '''
        Delivers a send request

        :param order_mem: reference to a Order memory object.
        :return:
        '''
        # NOTE: the next.status, before send(), is IDLE. After send, is PENDING
        order_mem.next.status = FIXStatus.PENDING
        ENV.agents_actions[order_mem.client].append_msg(('new', order_mem))
        return True

    @staticmethod
    def book(symbol):
        '''
        Return an Instance of Book class related to the symbol passed

        :param symbol: String identifying the symbol this leg will manage
        :return: Book objebct
        '''
        # TODO: change the return to be a neutrino book object
        return ENV.get_order_book(symbol, False)

    # @staticmethod
    # def get_book(symbol):
    #     '''
    #     Return an Instance of Book class related to the symbol passed

    #     :param symbol: String identifying the symbol this leg will manage
    #     :return: Book objebct
    #     '''
    #     # TODO: change the return to be a neutrino book object
    #     return ENV.get_order_book(symbol, False)

    @staticmethod
    def getTrades(book_obj, b_from_candles=False):
        '''
        Return an Instance of TradeBuffer class related to the book passed

        :param book_obj: neutrino Book.
        :*param b_from_candles: boolean. Only exist in simulation
        :return: TradeBuffer objebct
        '''
        return ENV.get_last_trades(book_obj, b_from_candles)

    # @staticmethod
    # def get_trades(book_obj, b_from_candles=False):
    #     '''
    #     Return an Instance of TradeBuffer class related to the book passed

    #     :param book_obj: neutrino Book.
    #     :*param b_from_candles: boolean. Only exist in simulation
    #     :return: TradeBuffer objebct
    #     '''
    #     return ENV.get_last_trades(book_obj, b_from_candles)

    @staticmethod
    def getSummary(book_obj, b_from_candles=False):
        '''
        Return an Instance of Summary class related to the book passed

        :param book_obj: neutrino Book.
        :*param b_from_candles: boolean. Only exist in simulation
        :return: Summary objebct
        '''
        obj_rtn = Summary()
        obj_rtn.bidCount = book_obj.get_counts('BID', 'Total')
        obj_rtn.askCount = book_obj.get_counts('ASK', 'Total')
        obj_rtn.statusChanged = 0  # is 1 only when the book status changes

        # NOTE: fileds presented just in simulation (for now)
        obj_rtn.newBidOrders = book_obj.get_counts('BID', 'New')
        obj_rtn.canceledBidOrders = book_obj.get_counts('BID', 'Canceled')
        obj_rtn.replacedBidOrders = book_obj.get_counts('BID', 'Replaced')

        obj_rtn.newAskOrders = book_obj.get_counts('ASK', 'New')
        obj_rtn.canceledAskOrders = book_obj.get_counts('ASK', 'Canceled')
        obj_rtn.replacedAskOrders = book_obj.get_counts('ASK', 'Replaced')

        i_aux = book_obj.get_counts('BID', 'Partially Filled')
        i_aux += book_obj.get_counts('BID', 'Filled')
        obj_rtn.tradeCountIncrement = i_aux

        # NOTE: As I just sent the incremental, the tradeCount is always the
        # size of the TradeBuffer. However, in the production, it should be
        # used to calculate the index to iterate in the trading list
        if b_from_candles:
            obj_rtn.tradeCount = len(book_obj.last_trades_aux)
        else:
            obj_rtn.tradeCount = len(book_obj.last_trades)

        return obj_rtn

    @staticmethod
    def add(symbol, trade_callback='default', book_callback='default',
            trade_buffer_size=64, i_id=11):
        '''
        Create new callbacks to the symbol's book and trades updates

        :param symbol: string.
        :param trade_callback: function.
        :param book_callback: function.
        :param trade_buffer_size: int.
        :param agent_id: integer. Only valid to simulations
        '''
        s_err = '[neutrino error] Symbol %s is not registered' % symbol
        assert symbol in ENV.l_instrument, s_err
        d_pcbacks = fx.pending_callbacks
        d_scbacks = fx.symbols_callbacks
        if i_id not in d_scbacks:
            d_scbacks[i_id] = set()
            fx.trade_callback_used[i_id] = None
        if i_id not in d_pcbacks:
            d_pcbacks[i_id] = init_pending_cbacks()

        this_agent = ENV.agents_actions[i_id].owner
        if hasattr(ENV.agents_actions[i_id].owner, 'agent'):
            this_agent = ENV.agents_actions[i_id].owner.agent
        d_pcbacks[i_id]['checked'] = False
        if trade_callback and trade_callback != 'default':
            d_scbacks[i_id].add(symbol)
            d_pcbacks[i_id]['trade'].append([symbol, trade_callback])
            fx.trade_callback_used[i_id] = trade_callback
            # self.last_trades = TradeBuffer()
            # self.last_trades_aux = TradeBuffer()
        elif trade_callback == 'default':
            d_pcbacks[i_id]['trade'].append([symbol, this_agent.on_data])
        if book_callback and book_callback != 'default':
            d_scbacks[i_id].add(symbol)
            d_pcbacks[i_id]['book'].append([symbol, book_callback])
        elif book_callback == 'default':
            d_pcbacks[i_id]['book'].append([symbol, this_agent.on_data])

        # NOTE: use fx.online here is not quite right, but it is OK for sim
        return InstrumentRegister(symbol, b_ready=fx.isOnline(symbol))

    @staticmethod
    def remove(symbol_propty, i_id=11):
        symbol = symbol_propty._s_instr
        # remove from fx
        d_pcbacks = fx.pending_callbacks
        d_scbacks = fx.symbols_callbacks
        if i_id in d_scbacks and i_id in d_pcbacks:
            d_pcbacks[i_id]['trade'] = []
            d_pcbacks[i_id]['book'] = []
            if not len(d_pcbacks[i_id]['other']):
                d_pcbacks.pop(i_id)
            if symbol in d_scbacks[i_id]:
                d_scbacks[i_id].remove(symbol)

        # remove from environment
        ENV.remove_callback(trigger=Source.MARKET, i_id=i_id,
                            s_instr=symbol)
        s_err = '[neutrino info] Symbol %s removed' % symbol
        print(s_err)

    @staticmethod
    def get(symbol, i_id=11):
        return InstrumentRegister(symbol)

    @staticmethod
    def every(name, interval, callback, i_id=11):
        '''
        Schedule a new callback to run every interval specified

        :param name: string.
        :param interval: neutrino.Interval object.
        :param callback: function.
        :param agent_id: integer. Only valid to simulations
        '''
        # initialize callbacks dict, if needed
        d_pcbacks = fx.pending_callbacks
        d_tcbacks = fx.time_callbacks
        if i_id not in d_tcbacks:
            d_tcbacks[i_id] = set()
        if i_id not in d_pcbacks:
            d_pcbacks[i_id] = init_pending_cbacks()

        # append the callback
        schdl = SchaduleInfos(name)
        schdl.kind = 'every'
        schdl.every = interval

        d_tcbacks[i_id].add(schdl)
        d_pcbacks[i_id]['checked'] = False
        d_pcbacks[i_id]['other'].append([schdl, callback])

        obj_rtn = ScheduledFunction(
            function=callback, s_name=name, i_interval=interval)
        schdl._scheduled_obj = obj_rtn
        return obj_rtn

    @staticmethod
    def at(name, hour, minute, callback, i_id=11):
        '''
        Schedule a new callback to run at the time specified

        :param name: string.
        :param hour: integer.
        :param minute: integer.
        :param callback: function.
        :param agent_id: integer. Only valid to simulations
        '''
        # initialize callbacks dict, if needed
        d_pcbacks = fx.pending_callbacks
        d_tcbacks = fx.time_callbacks
        if i_id not in d_tcbacks:
            d_tcbacks[i_id] = set()
        if i_id not in d_pcbacks:
            d_pcbacks[i_id] = init_pending_cbacks()

        # append the callback
        schdl = SchaduleInfos(name)
        schdl.kind = 'at'
        schdl.at = hour * 60**2 + minute * 60
        d_tcbacks[i_id].add(schdl)
        d_pcbacks[i_id]['checked'] = False
        d_pcbacks[i_id]['other'].append([schdl, callback])

        obj_rtn = ScheduledFunction(
            function=callback, s_name=name, i_hour=hour, i_minute=minute)
        schdl._scheduled_obj = obj_rtn
        return obj_rtn

    @staticmethod
    def remove_schedule(name, i_id=11):
        '''
        Remove

        :param name: string.
        :param agent_id: integer. Only valid to simulations
        '''
        # remove from fx
        d_pcbacks = fx.pending_callbacks
        d_tcbacks = fx.time_callbacks
        b_removed = True
        if i_id in d_tcbacks:
            # b_removed = True
            d_pcbacks[i_id]['other'] = [
                [n, c] for n, c in d_pcbacks[i_id]['other'] if n != name]
            d_tcbacks[i_id].remove(name)
            # if ((not len(d_pcbacks[i_id]['trade'])) and
            #     (not len(d_pcbacks[i_id]['book']))):
            #     d_pcbacks.pop(i_id)

        # remove from environment
        ENV.remove_callback(trigger=Source.IDLE, i_id=i_id,
                            s_name=name)
        s_err = '[neutrino info] Schedule %s removed' % name
        print(s_err)
        return b_removed

    @staticmethod
    def get_schedules(i_id=11):
        '''
        Get all scheduled functions

        :param agent_id: integer. Only valid to simulations
        '''
        # remove from fx
        d_pcbacks = fx.pending_callbacks
        d_tcbacks = fx.time_callbacks[i_id]
        l_funcs = [c._scheduled_obj for n, c in d_pcbacks[i_id]['other']]
        l_funcs += [c._scheduled_obj for c in list(d_tcbacks)]
        return l_funcs

    @staticmethod
    def add_bar(symbol, bar_count, interval, callback='default', i_id=11):
        '''
        Subscribe the data streaming of a new candle

        :param s_symbol: string. symbol to be subscribed
        :param interval: integer. The interval of the candle, in minutes
        :param bar_count: integer.
        :param callback: function.
        :return: CandleRegister.
        '''

        interval = int(interval)
        s_err = '[neutrino error] Symbol %s is not registered' % symbol
        s_alias = '%s_%s_%s' % (symbol, interval, bar_count)
        assert symbol in ENV.l_instrument, s_err
        d_pcbacks = fx.pending_callbacks
        d_scbacks = fx.symbols_callbacks
        if i_id not in d_scbacks:
            d_scbacks[i_id] = set()
        if i_id not in d_pcbacks:
            d_pcbacks[i_id] = init_pending_cbacks()

        this_agent = ENV.agents_actions[i_id].owner
        if hasattr(ENV.agents_actions[i_id].owner, 'agent'):
            this_agent = ENV.agents_actions[i_id].owner.agent
        d_pcbacks[i_id]['checked'] = False
        if callback and callback != 'default':
            d_scbacks[i_id].add(symbol)
            d_pcbacks[i_id]['candle'].append([symbol, callback])
        elif callback == 'default':
            d_scbacks[i_id].add(symbol)
            if isinstance(fx.trade_callback_used[i_id], type(None)):
                func_callback = this_agent.on_data
            else:
                func_callback = fx.trade_callback_used[i_id]
            d_pcbacks[i_id]['candle'].append([symbol, func_callback])

        obj_candle = ENV.candles.subscribe(
            s_symbol=symbol,
            interval=interval,
            i_nbars=bar_count,
            s_alias=s_alias)
        obj_candle.v3_obj = CandleRegister(obj_candle, False)
        obj_candle.v3_obj.properties.symbol = symbol
        obj_candle.v3_obj.properties.interval = interval
        obj_candle.v3_obj.properties.bar_count = bar_count
        return obj_candle.v3_obj

    @staticmethod
    def get_bar(symbol, bar_count, interval):
        '''
        Subscribe the data streaming of a new candle

        :param s_symbol: string. symbol to be subscribed
        :param interval: neutrino.CandleInterval object. The candle interval
        :param bar_count: integer.
        :param callback:
        :return: CandleData.
        '''
        s_alias = '%s_%s_%s' % (symbol, interval, bar_count)
        obj_candle = ENV.candles.get_candle(s_alias=s_alias)

        return obj_candle.v3_obj

    @staticmethod
    def remove_bar(candle_propty):
        '''
        Remove the CandleProperty object passed

        :param candle_propty: CandleProperty object.
        :return: boolean.
        '''
        symbol = candle_propty._bar_obj.symbol_name
        interval = candle_propty._bar_obj.i_interval
        bar_count = candle_propty._bar_obj.i_nbars
        s_alias = '%s_%s_%s' % (symbol, interval, bar_count)
        obj_candle = ENV.candles.get_candle(s_alias=s_alias)
        b_remove = False
        if not isinstance(obj_candle, type(None)):
            b_remove = True
            ENV.candles.reset(this_candle=obj_candle)

        return b_remove

    @staticmethod
    def subscribeIndicator(symbol, stype, conf, begin):
        '''
        Subscribe new indicator or candle

        :param symbol: string.
        :param stype: string.
        :param conf: string.
        :param begin: float.
        :param agent_id: integer. Only valid to simulations
        '''
        ENV.addIndicator(symbol, stype, conf, begin)

    @staticmethod
    def unsubscribeIndicator(symbol, stype, conf, begin):
        '''
        Subscribe new indicator or candle

        :param symbol: string.
        :param stype: string.
        :param conf: string.
        :param begin: float.
        '''
        ENV.excludeIndicator(symbol, stype, conf, begin)

    class Data(object):
        '''
        Data present in a line of a Book
        - price :
        - orderID :
        - quantity :
        - detail :
        '''
        def __init__(self):
            self.orderID = 'abc'
            self.quantity = 0
            self.price = 0
            self.detail = ''

        def __str__(self):
            s_msg = 'Data(orderid={} qty={} price={} detail={}'
            return s_msg.format(self.orderID, self.quantity, self.price,
                                self.detail)

    class DataList(object):
        '''
        A vector (or list) of Data. See DataTypes.hpp
        '''
        def __init__(self):
            self.dataEntities = []

    class Callback(object):
        '''
        A python application must have a callback interface that will be
        instantiated by the API and called certain methods as events arrive
        from the network.
        '''

        def bidSide(self, source, book=None):
            pass

        def askSide(self, source, book=None):
            '''
            A callback receiving updates on books or on idle events.

            :param source: Instance of class Source: IDLE = 0, MARKET = 1,
                ORDER = 2, COMMAND = 3
            :param book: Instance of Book class,
            :return:
            '''
            pass

        def command(self):
            pass

        def symbolsLoaded(self):
            pass

        def orderFilled(self):
            pass

        def orderUpdated(self):
            pass

        def setParameter(self):
            pass


'''
Initialize structures
'''

# Initiate structure to be used by an agent. It complies to the new neutrino
#  cluster sintaxe

market = Market()
utils = Utils()
oms = Oms()
position = Position()


'''
End Initialization
'''
