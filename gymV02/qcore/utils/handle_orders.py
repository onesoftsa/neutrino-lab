#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Implement the classes to handle the agent positions and orders related to each
instrument subscribed, as well as the functions required to  include new orders
in the market and manipulate them


@author: ucaiado

Created on 07/05/2018
'''

import os
import yaml
from itertools import cycle
from collections import namedtuple

from neutrinogym.qcore import PROD

if not PROD:
    from neutrinogym import neutrino
    from neutrinogym.neutrino import fx
else:
    import neutrino
    from neutrino import fx

from .neutrino_utils import (neutrino_now, Logger)
from .handle_bkoffice import (update_position, account_active_qty,
                              update_order_ctrls, priority_changed)


import pdb

'''
Begin help functions
'''


def create_usrdata(d_tokens, i_new_id=None, f_crrprice=None):
    '''
    return a dictionary to be stored in userdata attribute from a Order object

    :param d_tokens: dict. informations about the order
    :param i_id: int. the new/current ID of the order
    '''
    i_id = d_tokens.get('order_id')
    if not i_new_id:
        i_new_id = d_tokens.get('order_id')
    if not f_crrprice:
        f_crrprice = d_tokens.get('price')
    d_aux = {'p': f_crrprice, 'new_p': d_tokens.get('price'), 'id': i_id,
             'new_id': i_new_id}
    return d_aux

'''
End help functions
'''


class OrderStack(object):
    '''
    Handle the stack of orders used by the agent
    '''
    def __init__(self, l_orders):
        '''
        Initialize an OrderStack object

        :param l_orders: list. list of neutrino Order objects
        '''
        self.all_orders = l_orders
        self.iterator = cycle(l_orders)
        self.idx = 0

    def __iter__(self): return self

    def next(self):
        '''
        Implement the behavior of __iter__ method
        '''
        return self.__next__()

    def __next__(self):
        '''
        Implement the behavior of __iter__ method
        '''
        # Just return orders that are not alive
        for idx, order in enumerate(self.iterator):
            self.idx = idx
            if not order.isAlive() and not order.isPending():
                return order


class Instrument(object):
    '''
   A representation of an instrument traded by the agent. Handle the
   bookkeeping of all orders and positions related to this security
    '''

    def __init__(self, s_symbol, i_stack):
        '''
        Instantiate and Instrument object. Save all parameters as attributes

        :param s_symbol: string. The instrument traded
        :param i_stack: integer. The number of orders objects to initiate
        '''
        self.symbol_name = str(s_symbol)
        self._ready = False
        self._ord_stack = {'BID': None, 'ASK': None}
        self._orders = {}
        self._max_orders = i_stack

        # initialize order control variables
        self._ready = True
        self._counting = {'Exec': 0, 'Msg': 0}
        self._active_qty = {'BID': 0, 'ASK': 0}
        self._prices = {'BID': {}, 'ASK': {}}

        # instatiate position control variables
        l_aux = ['qAsk', 'Ask', 'qBid', 'Bid']
        self._position = dict(zip(l_aux, [0 for _ in l_aux]))
        self._init_pos = dict(zip(l_aux, [0 for _ in l_aux]))
        self._open_pos = {'BID': [], 'ASK': []}

        # set instruments parameters
        self.min_tick_size = 0.01
        self.min_lot_size = 100

        # NOTE: book data should be here?
        self.last_trade = None

        # new API
        self.logger = None

    def on_symbols_load(self, agent):
        '''
        Initiate attributes that required the availability of the books traded

        :param agent: Agent object.
        '''
        # instatiate initial list of orders
        self._ord_stack = {'BID': None, 'ASK': None}
        s_symbol = self.symbol_name
        for side in [neutrino.Side.ASK, neutrino.Side.BID]:
            l_aux = []
            for _ in range(1, self._max_orders + 1):
                order = neutrino.Order(side)
                if PROD:
                    fx.configureOrder(s_symbol, 0, order)  # production
                else:
                    fx.configureOrder(s_symbol, 0, order, agent.i_id)  # simul
                l_aux.append(order)
            self._ord_stack[str(side)] = OrderStack(l_aux)

        # set metaparameters for this instrument
        security_info = fx.book(self.symbol_name).security()
        self.min_tick_size = security_info.priceIncrement
        self.min_lot_size = security_info.minOrderQty

    def get_my_order_by_id(self, i_id):
        '''
        Return the neutrino Order related to the id passe

        :param i_id: integer. Inter order id
        '''
        return self._orders.get(i_id, None)

    def get_my_prices_on(self, s_side):
        '''
        Get a list of unique prices of the agent active orders. Return an
        empty list if there is no orders

        :param s_side: string. Can be BID or ASK
        '''
        l_prices = self._prices[s_side].keys()
        if not l_prices:
            return []
        b_isbid = (s_side == 'BID')
        return sorted(l_prices, reverse=b_isbid)

    def get_my_orders_by_price(self, s_side, f_price):
        '''
        Get active orders in the required price. Return an ampty list if there
        is no orders at the price

        :param s_side: string. Can be BID or ASK
        :param f_price: float. Price desired
        '''
        l_orders = self._prices[s_side].get(f_price)
        if not l_orders:
            return []
        return l_orders

    def get_my_orders_by_side(self, s_side):
        '''
        Get active orders in the required side. Return an ampty list if there
        is no orders available

        :param s_side: string. Can be BID or ASK
        :param f_price: float. Price desired
        '''
        l_orders = self._prices[s_side].items()
        # l_orders = self._prices[s_side].values()
        if not l_orders:
            return []

        b_isbid = (s_side == 'BID')
        l_orders = [item for _, sublist in sorted([(key, val) for (key, val)
                    in l_orders], reverse=b_isbid) for item in sorted(sublist)]
        # l_orders = [item for sublist in l_orders for item in sublist]
        return l_orders

    def get_nmsgs(self):
        '''
        Get number of messages sent to the market until now. Include new
        orders, cancellations, executions, partial executions and rejections

        :param symbol: string. The name of the instrument
        '''
        return self._counting['Msg']

    def get_nexec(self):
        '''
        Get number of executions in a particular instrument, including filled
        and partial filled orders

        :param symbol: string. The name of the instrument
        '''
        return self._counting['Exec']

    def get_active_qty(self, s_side):
        '''
        Get opened position and volume to the given instrument

        :param s_side: string. Can be BID or ASK
        '''
        return self._active_qty[s_side]

    def get_position(self, b_include_init=True):
        '''
        Return the current position in a specific instrument

        :param s_symbol: string. The intrument to recover the position
        :return: integer. The instrument current position
        '''
        i_pos = self._position['qBid']
        i_pos -= self._position['qAsk']
        if b_include_init:
            i_pos += self._init_pos['qBid']
            i_pos -= self._init_pos['qAsk']
        return i_pos

    def set_initial_positions(self, agent, d_position):
        '''
        Set the initial position of this instrument

        :param d_position: disct. The position by instrument, including
        '''
        # for s_instr, d_pos in d_position.iteritems():
        #     if s_instr not in self._init_pos:
        #         s_msg = 'Agent.set_initial_positions(): '
        #         s_msg += '{} instrument not found'
        #         agent.print_debug_msg(s_msg.format(s_instr), True)
        #         continue
        i_qty = int(d_position['Q'])
        if i_qty < 0:
            self._init_pos['qAsk'] = abs(i_qty)
            self._init_pos['qBid'] = 0
            if 'P' in d_position and d_position['P'] != 0.:
                f_volume = float(d_position['P']) * abs(i_qty)
                self._init_pos['Ask'] = f_volume
                self._init_pos['Bid'] = 0
        elif i_qty > 0:
            self._init_pos['qAsk'] = 0
            self._init_pos['qBid'] = abs(i_qty)
            if 'P' in d_position and d_position['P'] != 0.:
                f_volume = float(d_position['P']) * abs(i_qty)
                self._init_pos['Ask'] = 0
                self._init_pos['Bid'] = f_volume
        if i_qty != 0:
            s_msg = self.logger['position']
            s_msg = s_msg.format(self.symbol_name, d_position)
            print(s_msg)

    def update_position(self, order, f_lastpx, f_lastqty):
        '''
        Update instrument position

        :param order: Neutrino Order object.
        :param f_lastpx: float.
        :param f_lastqty: integer.
        '''
        update_position(order.symbol, str(order.side), f_lastpx, f_lastqty,
                        self._position, self._open_pos)

    def update_order_ctrls(self, order):
        '''
        Update order controls

        :param order: Neutrino Order object.
        '''
        update_order_ctrls(order, self._orders, self._prices)

    def update_active_qty(self, order, s_type, i_qty=0):
        '''
        Update the total active qty in the order book

        :param order: neutruno Order object
        :param s_type: string. source of change in _active_qty attribute
        :param *i_qty: int. Last qty executed
        '''
        s_intr = order.symbol
        s_side = str(order.side)
        # import pdb; pdb.set_trace()
        # NOTE: it doesnt work as expected. when occurs too many executions
        #   this control miscalculate the active quantity
        account_active_qty(
            self._active_qty, s_intr, s_side, s_type, i_qty,
            len(self._prices[s_side]))

    def __str__(self):
        return '<{} instance>.{}'.format(type(self).__name__, self.symbol_name)


class OrderHandler(object):
    '''
    Handle the main interations with order objects
    '''

    # orders time in force (tif) options available
    _tif = {'day': neutrino.TimeInForce.DAY,
            'fak': neutrino.TimeInForce.FAK,
            'fok': neutrino.TimeInForce.FOK}

    _tif2str = {
        neutrino.TimeInForce.DAY: 'day',
        neutrino.TimeInForce.FAK: 'fak',
        neutrino.TimeInForce.FOK: 'fok'}

    _send_cancel_acc = {'S': fx.send, 'C': fx.cancel}

    logger = None

    def set_owner(self, agent):
        '''
        Set the OrderHndler owner
        '''
        self.agent = agent
        # if hasattr(agent, '_mlogs'):
        #     self.logger = Logger(agent._mlogs)
        self.last_order_id = 0

    def get_instrument_from(self, order=None, d_tokens=None, s_symbol=None,
                            candle=None):
        '''
        Return the instrument traded by the agent

        :param order: Neutrino Order object.
        :param d_tokens: dict.
        :param s_symbol: string.
        :param candle: CandleData object.
        '''
        if candle:
            return self.agent._instr_stack.get(candle.symbol_name, None)
        if s_symbol:
            return self.agent._instr_stack.get(s_symbol, None)
        if not order and d_tokens:
            return self.agent._instr_stack.get(d_tokens.get('symbol'), None)
        if not d_tokens and order:
            return self.agent._instr_stack.get(order.symbol, None)
        return None

    def send_cancel_acc(self, order, s_interact):
        '''
        Interact with the market and/or account the number of messages or
        executions that already had happened. Return if any action took place

        :param order: neutruno Order object. the order filled
        :param s_interact: string. kind of interaction with market (C, S, E)
        '''
        instr = self.get_instrument_from(order)
        if s_interact == 'E':
            instr._counting['Exec'] += 1
            return False
        instr._counting['Msg'] += 1
        if self._send_cancel_acc[s_interact](order):
            s_state = None
            if order.next:
                s_state = str(order.next.status)
            # print 'Agent.send_cancel_acc(): Update order {}'.format(order)
            update_order_ctrls(order, instr._orders, instr._prices,
                               s_state)
            return True
        return False

    def createorder(self, instr, side, d_tokens):
        '''
        Send a new order to the LOB

        :param side: neutrino Side. Can be BID or ASK
        :param d_tokens: dict. the parameters to the new order.
        '''
        # check if there is a order using the same ID
        b_t = hasattr(self.agent, 'is_offline')
        if b_t and self.agent.is_offline():
            return
        if 'order_id' not in d_tokens:
            self.agent.last_order_id += 1
            d_tokens['order_id'] = self.agent.last_order_id
        old_order = instr._orders.get(d_tokens.get('order_id'))
        if old_order:
            s_msg = self.logger['errcreateorder']
            if b_t:
                self.agent.print_debug_msg(s_msg, True, True)
            self.cancel_order(old_order)
            return
        # cerate the new order
        symbol = d_tokens.get('symbol')
        _ = instr._ord_stack  # just to check
        order = next(instr._ord_stack[str(side)])
        order.userData = create_usrdata(d_tokens)
        fx.attachToLeg(order, 0)
        self.process_parameters(order, d_tokens)
        # print 'Agent.createorder(): send_cancel_acc'
        if self.send_cancel_acc(order, 'S'):
            i_qty = int(d_tokens.get('qty'))
            instr.update_active_qty(order, 'N', i_qty)
            s_time = (neutrino_now(True))[:-3]  # simulation
            # s_time = str(neutrino_now())  # production
            s_msg = self.logger['createorder'].format(
                s_time,
                str(side),
                symbol,
                d_tokens.get('order_id'),
                d_tokens.get('qty'),
                d_tokens.get('price')
                )
            if b_t:
                self.agent.print_debug_msg(s_msg, True)
            else:
                print(s_msg)
        return order.userData['id']

    def new_order(self, instr, s_side, f_price, i_qty, s_tif='day',
                  s_type='limit', **kwargs):
        '''
        Include a new order in the symbol, side and price passed

        :param s_symbol: string. The name of the instrument
        :param s_side: string. Can be BID or ASK
        :param f_price: float. price
        :param i_qty: integer. Qty of the order
        :param s_tif: string. Time in force. Can be day, fak or fok
        :param s_type: string. Order Type. Currently, can be only 'limit'. In
            the future, it can include limit, stop, etc.
        '''
        self.last_order_id += 1
        d_tokens = {'symbol': instr.symbol_name,
                    'order_id': self.last_order_id,
                    'tif': s_tif,
                    'qty': i_qty,
                    'price': f_price}
        i_id = self.createorder(instr, s_side, d_tokens)
        return i_id

    def modify_order(self, order=None, d_tokens=None, f_price=None, i_qty=None,
                     s_tif='day', s_type='limit', **kwargs):
        '''
        Modify an existing order in the LOB, if it is alive. If d_tokens is not
        provided, order, price qty are required

        :param *d_tokens: dict. The new order's parameters
        :param *order: Order. A neutrino Order object
        :param *f_price: float. The new price
        :param *i_qty: int. The new qty
        :param *s_tif: string. The new tif
        :param s_type: string. Order Type. Currently, can be only 'limit'. In
            the future, it can include limit, stop, etc.
        '''
        b_t = hasattr(self.agent, 'is_offline')
        if b_t and self.agent.is_offline():
            return
        if order and isinstance(order, type(namedtuple)):
            order = order.neutrino_order
        instr = self.get_instrument_from(d_tokens=d_tokens, order=order)
        i_new_id = order.userData['id']
        if not order:
            order = instr._orders.get(d_tokens.get('order_id'))
        # TODO: check if it works
        if not order.current or not order.current.qty:
            return
        if not d_tokens:
            d_tokens = {'order_id': order.userData['id'],
                        'qty': order.current.qty,
                        'price': order.userData['p'],
                        'tif': order.current.timeInForce}
            if i_qty:
                d_tokens['qty'] = i_qty
            if f_price:
                d_tokens['price'] = f_price
            if s_tif:
                d_tokens['tif'] = s_tif
        # if order and order.isAlive() and not order.isPending():
        if order and not order.isPending():
            # check if should include a new order ID to this order
            if priority_changed(order, d_tokens):
                # NOTE: Let's check if I can keep the original ID
                self.last_order_id += 1
                i_new_id = self.last_order_id
                # i_new_id = d_tokens.get('order_id')
                order.userData = create_usrdata(d_tokens, i_new_id,
                                                order.userData['p'])
            else:
                order.userData = create_usrdata(d_tokens)
            fx.attachToLeg(order, 0)  # create a new transation
            self.process_parameters(order, d_tokens)
            i_cumqty = order.current.cumQty
            i_cumqty = i_cumqty if i_cumqty and abs(i_cumqty) < 10**7 else 0
            i_remain_qty = order.current.qty - i_cumqty
            instr.update_active_qty(order, 'PM', i_remain_qty)
            if self.send_cancel_acc(order, 'S'):
                i_cumqty = order.next.cumQty
                i_cumqty = i_cumqty if i_cumqty and abs(i_cumqty) < 10**7 else 0
                i_currqty = order.next.qty
                i_currqty = i_currqty if abs(i_currqty) < 10**7 else 0
                i_remain_qty = i_currqty - i_cumqty
                instr.update_active_qty(order, 'M', i_remain_qty)
                s_time = (neutrino_now(True))[:-3]  # simulation
                # s_time = str(neutrino_now())  # production
                s_msg = self.logger['modify'].format(
                    s_time,
                    str(order.side),
                    order.symbol,
                    d_tokens.get('order_id'),
                    d_tokens.get('qty'),
                    d_tokens.get('price')
                    )
                if b_t:
                    self.agent.print_debug_msg(s_msg, True, True)
                else:
                    print(s_msg)
        return i_new_id

    def cancel_order(self, order=None, d_tokens=None):
        '''
        Cancel an existing order in the LOB, if it is alive

        :param d_tokens: dict. The new order's parameters
        '''
        b_t = hasattr(self.agent, 'is_offline')
        instr = self.get_instrument_from(d_tokens=d_tokens, order=order)
        if order and isinstance(order, type(namedtuple)):
            order = order.neutrino_order
        if not order:
            order = instr._orders.get(int(d_tokens.get('order_id')))
        # if order and order.isAlive() and not order.isPending():
        if order and not order.isPending():
            s_time = (neutrino_now(True))[:-3]  # simulation
            # s_time = str(neutrino_now())  # production
            s_msg = self.logger['cancel'].format(
                s_time,
                order.side,
                order.symbol,
                order.userData['id']
                )
            if b_t:
                self.agent.print_debug_msg(s_msg, True, True)
            else:
                print(s_msg)
            fx.attachToLeg(order, 0)  # create a new transation
            # print 'Agent.cancel_order(): send_cancel_acc'
            self.send_cancel_acc(order, 'C')

    def cancel_orders_by_price(self, instr, s_side, f_price):
        '''
        Cancel all orders in a specific price from a specific instr and side

        :param instr: Instrument object.
        :param s_side: string. Can be BID or ASK
        :param f_price: float. price
        '''
        l_orders = instr._prices[s_side].get(f_price)
        if l_orders:
            for order_id in l_orders:
                order = instr._orders.get(order_id)
                # NOTE: specific for simulation.
                if not order:
                    return
                # end NOTE ######
                self.cancel_order(order)

    def cancel_orders_by_side(self, instr, s_side, b_ignore_best=False):
        '''
        Cancel all orders from an instrument and side

        :param instr: Instrument object.
        :param s_side: string. Can be BID or ASK
        :param *b_ignore_best: Bool. Not cancel the best price
        '''
        f_best_price = -1
        if b_ignore_best:
            if s_side == 'BID':
                if instr._prices[s_side].keys():
                    l_best_price = instr._prices[s_side].keys()
                    f_best_price = max(l_best_price)
            elif s_side == 'ASK':
                if instr._prices[s_side].keys():
                    l_best_price = instr._prices[s_side].keys()
                    f_best_price = min(l_best_price)
        for f_price in instr._prices[s_side].keys():
            if b_ignore_best and f_price == f_best_price:
                continue
            self.cancel_orders_by_price(instr, s_side, f_price)

    def cancel_instrument_orders(self, instr):
        '''
        Cancel all orders

        :param instr: Instrument object.
        '''
        for i_key in instr._orders:
            self.cancel_order(instr._orders[i_key])

    def cancel_all_orders(self):
        '''
        Cancel all orders
        '''
        for instr in self.agent._instr_stack.values():
            self.cancel_instrument_orders(instr)

    def process_parameters(self, order, d_tokens):
        '''
        Set additional parameters to the order passed

        :param order: neutruno Order object. the order filled
        :param d_tokens: dict. The new order's parameters.
        '''
        order.next.timeInForce = self._tif[d_tokens.get('tif')]
        order.next.qty = int(d_tokens.get('qty'))
        order.next.price = float(d_tokens.get('price'))
        # order.next.cumQty = order.current.cumQty if order.current else 0
        # ==== debug ====
        try:
            order.next.price = float(d_tokens.get('price'))
        except TypeError:
            s_msg = self.agent._mlogs['errparms'].format(d_tokens.get('price'))
            s_msg += '\n{}'
            s_msg = s_msg.format(d_tokens)
            self.agent.print_debug_msg(s_msg, True)
