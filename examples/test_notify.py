#!/usr/bin/python
# -*- coding: future_fstrings -*-
"""
...


commands:
set TestNotify max_position {"WDOH20":{"limit":3,"type_limit":"quantity"}} open_pos {"bid":true,"ask":true,"spread":10}

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

_MAP_SIDE = {
    'buy': neutrino.Side.BID, 'sell': neutrino.Side.ASK,
    'bid': neutrino.Side.BID, 'ask': neutrino.Side.ASK,
    'BID': neutrino.Side.BID, 'ASK': neutrino.Side.ASK}

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


def order2str(order_entry, s_txt):
    if isinstance(order_entry, type(None)):
        print('%s fail to find order %s' % (s_txt, s_id))
        return
    print(s_txt +
        f'order({order_entry.unique_id}): ' +
        f'side={order_entry.side},' +
        f'secondary_order_id={order_entry.secondary_order_id},' +
        f'type={order_entry.type},' +
        f'account={order_entry.account},' +
        f'symbol={order_entry.symbol},' +
        f'tif={order_entry.time_in_force},' +
        f'status={order_entry.status},' +
        f'price={order_entry.price},' +
        f'last_price={order_entry.last_price},' +
        f'qty={order_entry.quantity},' +
        f'filled_qty={order_entry.filled_quantity},' +
        f'leaves_qty={order_entry.leaves_quantity},' +
        f'last_qty={order_entry.last_quantity},' +
        f'alive={order_entry.is_alive()},' +
        f'pending={order_entry.is_pending()},' +
        f'dead={order_entry.is_dead()}')


def position2str(position_status):
    s_rtn = '  POSITION ===================\n'
    s_rtn += '    TOTAL:  net=%i,' % position_status.total.net
    s_rtn += 'net_price=%.2f [' % position_status.total.net_price
    s_rtn += 'qBid=%.2f,' % position_status.total.bid_quantity
    s_rtn += 'vBid=%.2f,' % position_status.total.bid_volume
    s_rtn += 'vAsk=%.2f,' % position_status.total.ask_volume
    s_rtn += 'qAsk=%.2f]\n' % position_status.total.ask_quantity

    s_rtn += '    PARTIAL:  net=%i,' % position_status.partial.net
    s_rtn += 'net_price=%.2f [' % position_status.partial.net_price
    s_rtn += 'qBid=%.2f,' % position_status.partial.bid_quantity
    s_rtn += 'vBid=%.2f,' % position_status.partial.bid_volume
    s_rtn += 'vAsk=%.2f,' % position_status.partial.ask_volume
    s_rtn += 'qAsk=%.2f]\n' % position_status.partial.ask_quantity


    s_rtn += '    INITIAL:  net=%i,' % position_status.initial.net
    s_rtn += 'net_price=%.2f [' % position_status.initial.net_price
    s_rtn += 'qBid=%.2f,' % position_status.initial.bid_quantity
    s_rtn += 'vBid=%.2f,' % position_status.initial.bid_volume
    s_rtn += 'vAsk=%.2f,' % position_status.initial.ask_volume
    s_rtn += 'qAsk=%.2f]\n' % position_status.initial.ask_quantity

    return s_rtn


def orderU2str(order_entry):
    if isinstance(order_entry, type(None)):
        print('%s fail to find order %s' % (s_txt, s_id))
        return
    return (
        f'order({order_entry.unique_id}): ' +
        f'symbol={order_entry.symbol},' +
        f'side={order_entry.side},' +
        f'secondary_order_id={order_entry.secondary_order_id},' +
        f'status={order_entry.status},' +
        f'last_price={order_entry.last_price},' +
        f'price={order_entry.price},' +
        f'qty={order_entry.quantity}')


def _process_check(agent, l_data, s_txt):
    s_cmd, s_id = l_data
    if s_id.isdigit():
        order_entry = neutrino.oms.get_order_by_id(int(s_id))
        order2str(order_entry, s_txt)

    elif 'price' == s_id[:5] and len(s_id) > 5:
        f_price = float(s_id[5:])
        l_orderids = neutrino.oms.get_live_orders(
            agent.my_symbol, price=f_price)
        if l_orderids:
            print(f'%s Find {len(l_orderids)} orders using price:' % s_txt)
        else:
            print('%s No order found' % s_txt)
        for order_entry in l_orderids:
            order2str(order_entry, '')

    elif 'side' == s_id[:4] and len(s_id) > 5:
        s_side = _MAP_SIDE[s_id[4:].lower()]
        l_orderids = neutrino.oms.get_live_orders(
            agent.my_symbol, side=s_side)
        if l_orderids:
            print(f'%s Find {len(l_orderids)} orders using side:' % s_txt)
        else:
            print('%s No order found' % s_txt)
        for order_entry in l_orderids:
            order2str(order_entry, '')


def _process_where(agent, l_data, s_txt):
    s_cmd, s_id = l_data
    if s_id.isdigit():
        order_entry = neutrino.oms.get_order_by_id(int(s_id))
        if isinstance(order_entry, type(None)):
            print('%s fail to find order %s' % (s_txt, s_id))
            return
        instr = neutrino.market.get(order_entry.symbol)
        if str(order_entry.side) == 'BID':
            l_ids = [x.order_id for x in instr.book.bid()]
        else:
            l_ids = [x.order_id for x in instr.book.ask()]
        i_my_ii = -1
        for ii, order_id in enumerate(l_ids):
            if ((i_my_ii == -1) and
                order_id <= order_entry.secondary_order_id):
                i_my_ii = ii
        print(
            f'my order with secid {order_entry.secondary_order_id} ' +
            f'is in position {i_my_ii}. The min ID in the book ' +
            f'is {min(l_ids)} and the order_entry secid type ' +
            f'is {type(order_entry.secondary_order_id)}')

def _process_cancel(agent, l_data, s_txt):
    s_cmd, s_id = l_data
    if s_id.isdigit():
        order_entry = neutrino.oms.get_order_by_id(int(s_id))
        if isinstance(order_entry, type(None)):
            print('%s fail to find order %s' % (s_txt, s_id))
        if int(s_id) == 1:
            i_id = neutrino.oms.cancel(order_entry)
        elif int(s_id) > 1:
            i_id = order_entry.cancel()
        if i_id >= 0:
            print('%s %s order %s(%i)' % (s_txt, s_cmd, s_id, i_id))
        else:
            print('%s %s fail order %s(%i)' % (s_txt, s_cmd, s_id, i_id))
    elif 'all' == s_id:
        l_orders = neutrino.oms.cancel_all()
        import pdb; pdb.set_trace()

    elif 'price' == s_id[:5] and len(s_id) > 5:
        f_price = float(s_id[5:])
        l_orders = neutrino.oms.cancel_all(
            agent.my_symbol, price=f_price)
        import pdb; pdb.set_trace()

    elif 'side' == s_id[:4] and len(s_id) > 5:
        s_side = _MAP_SIDE[s_id[4:]]
        l_orders = neutrino.oms.cancel_all(
            agent.my_symbol, side=s_side)

def _process_replace(agent, l_data, s_txt):
    s_cmd, s_id, s_price = l_data
    if s_id.isdigit() and s_price[0] == '@':
        order_entry = neutrino.oms.get_order_by_id(int(s_id))
        if isinstance(order_entry, type(None)):
            print('%s fail to find order %s' % (s_txt, s_id))
        if int(s_id) == 1:
            i_id = neutrino.oms.replace_limit_order(
                # order_entry,
                # float(s_price[1:]),
                # order_entry.quantity,
                # order_entry.time_in_force)
                order_entry,
                price=float(s_price[1:]),
                quantity=order_entry.quantity,
                time_in_force=order_entry.time_in_force)
        elif int(s_id) > 1:
            i_id = order_entry.replace_limit(
                # float(s_price[1:]),
                # order_entry.quantity,
                # order_entry.time_in_force)
                price=float(s_price[1:]),
                quantity=order_entry.quantity,
                time_in_force=order_entry.time_in_force)
        if i_id >= 0:
            print('%s %s order %s(%i)' % (s_txt, s_cmd, s_id, i_id))
        else:
            print('%s %s fail order %s(%i)' % (s_txt, s_cmd, s_id, i_id))


def process_raw_input(agent, s_txt):
    if s_txt == 'q':
        neutrino.utils.quit()
        return
    elif s_txt[0] == 'k' and s_txt[1:].isdigit():
        agent.i_keep_going = int(s_txt[1:])
        return
    l_data = s_txt.lower().split(' ')
    s_txt = '    %s[on_data]process_raw_input: ' % epoch2str(neutrino.utils.now())
    # send a new order
    if len(l_data) == 3 and l_data[0] in ['buy', 'sell']:
        s_side, s_qty, s_price = l_data
        if s_qty.isdigit() and s_price[0] == '@':
            if s_price[1:].replace('.', '').isdigit():
                i_id = neutrino.oms.send_limit_order(
                    symbol=agent.my_symbol,
                    side=_MAP_SIDE[s_side],
                    price=float(s_price[1:]),
                    time_in_force=neutrino.TimeInForce.DAY,
                    quantity=int(s_qty))
                if i_id >= 0:
                    print('%s %s %s of something at %s using order %i' % (
                        s_txt, s_side, s_qty, s_price[1:], i_id))
                elif i_id < 0:
                    print('%s fail to %s due %s' % (
                        s_txt, s_side, i_id))

    # check order state
    if len(l_data) == 2 and l_data[0] == 'check':
        _process_check(agent, l_data, s_txt)

    # check order position
    if len(l_data) == 2 and l_data[0] == 'where':
        _process_where(agent, l_data, s_txt)

    # cancel orders
    if len(l_data) == 2 and l_data[0] == 'cancel':
        _process_cancel(agent, l_data, s_txt)

    # replace orders
    if len(l_data) == 3 and l_data[0] == 'replace':
        _process_replace(agent, l_data, s_txt)



'''
End help functions
'''


class TestNotify(object):
    def __init__(self):
        # initialize some variables
        print('__init__', flush=True)
        self.i_count = 0
        self.i_count2 = 0
        self.i_keep_going = 1
        self._config = {}
        self._name = ''
        self.all_orders = {'BID': {}, 'ASK': {}}
        self._time_to_quit = False
        if sys.version_info.major == 2:
            self.require_input = raw_input
        elif sys.version_info.major == 3:
            self.require_input = input
        self._spread = 0

    # new callbacks
    def initialize(self, symbols):
        print('initialize', flush=True)
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

        print('\n\n    symbols added: ', self.symbols2, '\n\n', flush=True)

    def on_data(self, update):
        # print('on_data', flush=True)
        # check if all structures is ready to be used
        this_instr = self.instr[self.my_symbol]
        if not (this_instr.ready()) or (self.my_symbol != update.symbol):
            return

        # print every PRINT_EVERY counts
        self.i_count += 1
        if self.i_count % (PRINT_EVERY * self.i_keep_going) > 0:
            print('.', end="", flush=True)
            return
        self.i_keep_going = 1

        if self._time_to_quit and self.i_count > 1000:
            # return
            for s_symbol in self.symbols:
                i_out = neutrino.oms.cancel_all(symbol=s_symbol)
                print('cancel orders from %s: %i' % (s_symbol, i_out))
            print('\n...quitting!!', flush=True)
            neutrino.utils.quit()
            return
        elif not self._time_to_quit and self._config and self.i_count > 100:
            print(book2str(self, this_instr.book.sequence), flush=True)
            this_position = neutrino.position.get(update.symbol)
            this_side=neutrino.Side.BID
            this_price=this_instr.book.ask[0].price
            this_price -= abs(self._spread)*this_instr.price_increment
            if this_position.initial.net > 0:
                this_side = neutrino.Side.ASK
                this_price=this_instr.book.bid[0].price
                this_price += abs(self._spread)*this_instr.price_increment
            i_id = neutrino.oms.send_limit_order(
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
            print(f'ORDER SENT WAS ID {i_id}...', flush=True)

    def order_update(self, order):
        print('...order update')

    def order_filled(self, order, lastpx, lastqty):
        print('... order filled')

    def set_parameters(self, config):
        print('set_parameters', flush=True)
        d_conf = json.loads(config)
        s_strat = list(d_conf.keys())[0]
        self._name = s_strat
        for s_main in d_conf[s_strat]:
            if s_main not in self._config:
                self._config[s_main] = {}
            if isinstance(d_conf[s_strat][s_main], dict):
                for s_in in d_conf[s_strat][s_main]:
                    self._config[s_main][s_in] = d_conf[s_strat][s_main][s_in]
            else:
                self._config[s_main] = d_conf[s_strat][s_main]
        if 'open_pos' in self._config:
            self._spread = self._config['open_pos'].get('spread', 0)
            print('!! new spread: %i' %  self._spread)

        print(('[set_parameters]', config), flush=True)

    def get_parameters(self):
        print(('[get_parameters]', self._config), flush=True)
        d_conf = {self._name: self._config}
        s_strat = self._name
        # try to hack the limit
        # try to hack the limit
        if 'open_pos' in d_conf[s_strat]:
            d_conf[s_strat]['open_pos']['ask'] = False  # should reflect
        if 'max_position' in d_conf[s_strat]:
            d_conf[s_strat]['max_position'] = {
                'WDOZ19': {'limit': 6, 'type_limit': 'quantity'}}  # should not
            d_conf[s_strat]['max_position']['WDOZ19']['limit'] = 6
        s_rtn = json.dumps(d_conf[s_strat])
        print(('[get_parameters]2:', s_rtn), flush=True)
        return s_rtn

    def finalize(self, reason):
        self.i_count2 += 1
        s_t = epoch2str(neutrino.utils.now())
        print(
            f'{s_t}finalize {self.i_count, self.i_count2}: {str(reason)}',
            flush=True)
        for s_symbol in self.symbols:
            i_out = neutrino.oms.cancel_all(symbol=s_symbol)
            print('cancel orders from %s: %i' % (s_symbol, i_out))
        # neutrino.fx.quit()
