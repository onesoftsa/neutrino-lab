#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Translate messages from files and from agents to the matching engine

@author: ucaiado

Created on 10/24/2016
"""

import numpy as np
from neutrinogym import neutrino
# import pprint


SIDE = {'BID': 'Buy Order', 'ASK': 'Sell Order'}
START_SESSION = 9*60**2 + 20*60
END_SESSION = 17*60**2 + 40*60


def translate_trades(row, my_book):
    '''
    Translate trade row into trades messages. Just translate the row if the
    trade occurs at the current best price

    :param row: dict. the original message from file
    :param my_book: LimitOrderBook object.
    '''
    # recover the price levels of interest
    l_msg = []
    gen_bk = None
    if row['order_side'] == 'Buy Order':
        if not my_book.best_bid:
            return l_msg
        f_best_price = my_book.best_bid[0]
        f_max = f_best_price + 0.01
        f_min = row['order_price']
        gen_bk = my_book.book_bid.price_tree.item_slice(f_min,
                                                        f_max,
                                                        reverse=True)
    else:
        if not my_book.best_ask:
            return l_msg
        f_best_price = my_book.best_ask[0]
        f_max = row['order_price'] + 0.01
        f_min = f_best_price
        gen_bk = my_book.book_ask.price_tree.item_slice(f_min,
                                                        f_max,
                                                        reverse=False)
    # recover the price levels of interest
    b_stop = False
    b_neutrino_order = False
    if not gen_bk:
        return None
    l_msg_debug = []
    for f_price, obj_price in gen_bk:
        # assert obj_price.order_tree.count <= 2, 'More than two offers'
        for idx_ord, obj_order in obj_price.order_tree.nsmallest(1000):
            # check if the order Id is different from the message
            d_compare = obj_order.d_msg
            if row['seq_order_number'] != d_compare['seq_order_number']:
                my_book.i_count_correction_by_trades += 1
                # create a trade to fill that order
                i_org_qty = d_compare['org_total_qty_order']
                i_traded_qty = d_compare['traded_qty_order']
                # === DRBUG ===
                l_msg_debug.append(d_compare)
                # =============
                i_sec_order = my_book.i_sec_ask
                if d_compare['order_side'] == 'Buy Order':
                    i_sec_order = my_book.i_sec_bid
                d_rtn = {'action': 'correction_by_trade',
                         'agent_id': d_compare['agent_id'],
                         'agressor_indicator': 'Passive',
                         'execution_type': 'Trade',
                         'idx': '000000000000000',
                         'instrument_symbol': d_compare['instrument_symbol'],
                         'is_today': d_compare['is_today'],
                         'member': d_compare['member'],
                         'order_date': d_compare['order_date'],
                         'order_datetime_entry': my_book.s_time[:-7],
                         'order_id': d_compare['order_id'],
                         'order_price': d_compare['order_price'],
                         'order_side': d_compare['order_side'],
                         'order_status': 'Filled',
                         'org_total_qty_order': i_org_qty,
                         'priority_indicator': d_compare['priority_indicator'],
                         'priority_seconds': my_book.f_time,
                         'priority_time': my_book.s_time[11:],
                         'secondary_order_id': d_compare['secondary_order_id'],
                         'seq_order_number': d_compare['seq_order_number'],
                         'session_date': my_book.s_time[:10],
                         'total_qty_order': 0,
                         'traded_qty_order': i_org_qty,
                         'order_qty': i_org_qty - i_traded_qty}
                # debug
                if not d_rtn['order_qty'] or d_rtn['order_qty'] < 0:
                    # print 'translate_trades'
                    # print d_rtn
                    # print i_qty_traded, i_qty_to_trade
                    # raise NotImplementedError
                    continue
                # end debug
                if 'neutrino_order' in d_compare:
                    b_neutrino_order = True
                    order = d_compare['neutrino_order']
                    order.status = neutrino.FIXStatus.PENDING
                    order.current.status = neutrino.FIXStatus.FILLED
                    order.current.isAlive = False
                    d_rtn['neutrino_order'] = order
                l_msg.append(d_rtn.copy())
            else:
                b_stop = True
                break
        if b_stop:
            break
        if not my_book.b_secure_changes:
            if not b_stop and not b_neutrino_order:
                return [row]
    l_msg.append(row)
    # === DEBUG ===
    # if len(l_msg_debug) > 1:
    #     print 'translate_trades(): Order should not be here'
    #     pprint.pprint(l_msg_debug)
    #     print
    # =============
    return l_msg


def translate_row(idx, row, my_book, s_side=None):
    '''
    Translate a line from a file of the bloomberg level I data

    :param idx: integer. Order entry step
    :param row: dict. the original message from file
    :param my_book: LimitOrderBook object.
    :param s_side*: string. 'BID' or 'ASK'. Determine the side of the trade
    '''
    # check if is a valid hour
    if row['priority_seconds'] < START_SESSION:
        return [row]
    if row['priority_seconds'] > END_SESSION:
        return [row]
    # check if there are other orders before the order traded
    b_trade1 = (row['execution_type'] == 'Trade')
    b_trade2 = (row['agressor_indicator'] == 'Passive')
    if b_trade1:
        my_book.i_count_crossed_books = 0
    if b_trade1 and b_trade2:
        return translate_trades(row, my_book)

    # check if the new row will cross the book
    b_status2check =  row['order_status'] in ['New', 'Replaced']
    if row['order_side'] == 'Sell Order' and b_status2check:
        if my_book.best_bid and row['order_price'] <= my_book.best_bid[0]:
            if (row['priority_seconds'] - my_book.f_time_crossed_books) > 0.005:
                my_book.f_time_crossed_books = row['priority_seconds']
                my_book.i_count_crossed_books += 1
            if my_book.i_count_crossed_books > 3 or row['agent_id'] != 10:
                my_book.f_time_crossed_books = row['priority_seconds']
                # print '\n\n!!! Ask order crossed BID'
                # import pdb; pdb.set_trace()
                return translate_trades_to_agent(row, my_book)
    elif row['order_side'] == 'Buy Order' and b_status2check:
        if my_book.best_ask and row['order_price'] >= my_book.best_ask[0]:
            if (row['priority_seconds'] - my_book.f_time_crossed_books) > 0.005:
                my_book.f_time_crossed_books = row['priority_seconds']
                my_book.i_count_crossed_books += 1
            if my_book.i_count_crossed_books > 3 or row['agent_id'] != 10:
                my_book.f_time_crossed_books = row['priority_seconds']
                # print '\n\n!!! Buy order crossed ASK'
                # import pdb; pdb.set_trace()
                return translate_trades_to_agent(row, my_book)

    # if row['seq_order_number'] == '7411839667717':
    #     import pdb; pdb.set_trace()
    return [row]


def correct_books(my_book):
    '''
    Return if should correct something on the book and the modifications needed

    :param my_book: LimitOrderBook object.
    '''
    # check if it is a valid hour
    b_should_update, d_updates = False, {'BID': [], 'ASK': []}
    if (my_book.f_time < START_SESSION) | (my_book.f_time > END_SESSION):
        return b_should_update, d_updates
    # check if the prices have crossed themselfs
    b_test = True
    # make sure that there are prices in the both sides
    if my_book.book_ask.price_tree.count == 0:
        b_test = False
    if my_book.book_bid.price_tree.count == 0:
        b_test = False
    if my_book.d_bid['execution_type'] == 'Trade':
        my_book.i_count_crossed_books = 0
        b_test = False
    if my_book.d_ask['execution_type'] == 'Trade':
        my_book.i_count_crossed_books = 0
        b_test = False
    if not my_book.best_bid:
        b_test = False
    if not my_book.best_ask:
        b_test = False
    # correct the books when they have crossed each other
    if not b_test:
        return b_should_update, d_updates
    if my_book.best_bid[0] != 0 and my_book.best_ask[0] != 0 and b_test:
        if my_book.best_bid[0] >= my_book.best_ask[0]:
            my_book.i_count_crossed_books += 1
            if my_book.i_count_crossed_books > 2:
                # as it doesnt know which side was there at first, it will
                # emulate a trade in the smaller side
                # TODO: Implement here when the books cross each other.
                # recover the price levels of interest
                l_msg = []
                i_idx_min = np.argmin([my_book.best_bid[1],
                                       my_book.best_ask[1]])
                l_book_min = [my_book.obj_best_bid, my_book.obj_best_ask]
                obj_price = l_book_min[i_idx_min]
                s_symbol = my_book.d_bid['instrument_symbol']
                for idx_ord, obj_order in obj_price.order_tree.nsmallest(1000):
                    # check if the order Id is different from the message
                    d_compare = obj_order.d_msg
                    # create a trade to fill that order
                    i_org_qty = d_compare['org_total_qty_order']
                    i_traded_qty = d_compare['traded_qty_order']
                    i_sec_order_id = d_compare['secondary_order_id']
                    i_priority_id = d_compare['priority_indicator']
                    s_symbol = d_compare['instrument_symbol']
                    i_sec_order = my_book.i_sec_ask
                    if d_compare['order_side'] == 'Buy Order':
                        i_sec_order = my_book.i_sec_bid
                    d_rtn = {'action': 'crossed_prices',
                             'agent_id': d_compare['agent_id'],
                             'agressor_indicator': 'Passive',
                             'execution_type': 'Trade',
                             'idx': '000000000000000',
                             'instrument_symbol': s_symbol,
                             'is_today': d_compare['is_today'],
                             'member': d_compare['member'],
                             'order_date': d_compare['order_date'],
                             'order_datetime_entry': my_book.s_time[:-7],
                             'order_id': d_compare['order_id'],
                             'order_price': d_compare['order_price'],
                             'order_side': d_compare['order_side'],
                             'order_status': 'Filled',
                             'org_total_qty_order': i_org_qty,
                             'priority_indicator': i_priority_id,
                             'priority_seconds': my_book.f_time,
                             'priority_time': my_book.s_time[11:],
                             'secondary_order_id': i_sec_order_id,
                             'seq_order_number': d_compare['seq_order_number'],
                             'session_date': my_book.s_time[:10],
                             'total_qty_order': 0,
                             'traded_qty_order': i_org_qty,
                             'order_qty': i_org_qty - i_traded_qty}
                    if 'neutrino_order' in d_compare:
                        order = d_compare['neutrino_order']
                        order.status = neutrino.FIXStatus.PENDING
                        order.current.status = neutrino.FIXStatus.FILLED
                        order.current.isAlive = False
                        d_rtn['neutrino_order'] = order
                    l_msg.append(d_rtn.copy())
                d_updates[['BID', 'ASK'][i_idx_min]] = l_msg
                b_should_update = True
    return b_should_update, d_updates


def correct_books_new(my_book):
    '''
    Return if should correct something on the book and the modifications needed

    :param my_book: LimitOrderBook object.
    '''
    # check if it is a valid hour
    b_should_update, d_updates = False, {'BID': [], 'ASK': []}
    if (my_book.f_time < START_SESSION) | (my_book.f_time > END_SESSION):
        return b_should_update, d_updates
    # check if the prices have crossed themselfs
    b_test = True
    # make sure that there are prices in the both sides
    if my_book.book_ask.price_tree.count == 0:
        b_test = False
    if my_book.book_bid.price_tree.count == 0:
        b_test = False
    if my_book.d_bid['execution_type'] == 'Trade':
        my_book.i_count_crossed_books = 0
        b_test = False
    if my_book.d_ask['execution_type'] == 'Trade':
        my_book.i_count_crossed_books = 0
        b_test = False
    if not my_book.best_bid:
        b_test = False
    if not my_book.best_ask:
        b_test = False
    # correct the books when they have crossed each other
    if not b_test:
        return b_should_update, d_updates
    if my_book.best_bid[0] != 0 and my_book.best_ask[0] != 0 and b_test:
        if my_book.best_bid[0] >= my_book.best_ask[0]:
            my_book.i_count_crossed_books += 1
            if my_book.i_count_crossed_books > 2:
                # as it doesnt know which side was there at first, it will
                # emulate a trade in the smaller side
                # TODO: Implement here when the books cross each other.
                # recover the price levels of interest
                l_msg = []
                i_idx_min = np.argmin([my_book.best_bid[1],
                                       my_book.best_ask[1]])
                i_idx_min2 = np.argmin([my_book.obj_best_bid.min_key(),
                                        my_book.obj_best_ask.min_key()])
                l_book_min = [my_book.obj_best_bid, my_book.obj_best_ask]
                obj_price = l_book_min[i_idx_min]  # smaller qty by price
                obj_price2 = l_book_min[i_idx_min2]  # older order in best pr
                # NOTE: a ordem mais antiga determina qual preco vai prevalecer
                # NOTE: a quantidade menor determina qual lado vai exaurir
                # NOTE: esta funcao deve comparar soh os best prices
                # O loop de fore que deve arrumar até estar tudo correto
                # preciso fazer loops separado, um para corrigir cada lado
                s_symbol = my_book.d_bid['instrument_symbol']
                for idx_ord, obj_order in obj_price.order_tree.nsmallest(1000):
                    # check if the order Id is different from the message
                    d_compare = obj_order.d_msg
                    # create a trade to fill that order
                    i_org_qty = d_compare['org_total_qty_order']
                    i_traded_qty = d_compare['traded_qty_order']
                    i_sec_order_id = d_compare['secondary_order_id']
                    i_priority_id = d_compare['priority_indicator']
                    s_symbol = d_compare['instrument_symbol']
                    i_sec_order = my_book.i_sec_ask
                    if d_compare['order_side'] == 'Buy Order':
                        i_sec_order = my_book.i_sec_bid
                    d_rtn = {'action': 'crossed_prices',
                             'agent_id': d_compare['agent_id'],
                             'agressor_indicator': 'Passive',
                             'execution_type': 'Trade',
                             'idx': '000000000000000',
                             'instrument_symbol': s_symbol,
                             'is_today': d_compare['is_today'],
                             'member': d_compare['member'],
                             'order_date': d_compare['order_date'],
                             'order_datetime_entry': my_book.s_time[:-7],
                             'order_id': d_compare['order_id'],
                             'order_price': d_compare['order_price'],
                             'order_side': d_compare['order_side'],
                             'order_status': 'Filled',
                             'org_total_qty_order': i_org_qty,
                             'priority_indicator': i_priority_id,
                             'priority_seconds': my_book.f_time,
                             'priority_time': my_book.s_time[11:],
                             'secondary_order_id': i_sec_order_id,
                             'seq_order_number': d_compare['seq_order_number'],
                             'session_date': my_book.s_time[:10],
                             'total_qty_order': 0,
                             'traded_qty_order': i_org_qty,
                             'order_qty': i_org_qty - i_traded_qty}
                    if 'neutrino_order' in d_compare:
                        order = d_compare['neutrino_order']
                        order.status = neutrino.FIXStatus.PENDING
                        # NOTE: preciso diferenciar entre filled e partial fill
                        # coisa que vai ser determinada de cara se a ordem
                        # estiver no menor lado se estiver no maior, a unica
                        # ordem partial filled vai ser a ultima, se for o caso
                        # (olhando para o order qty)
                        order.current.status = neutrino.FIXStatus.FILLED
                        order.current.isAlive = False
                        d_rtn['neutrino_order'] = order
                    l_msg.append(d_rtn.copy())
                d_updates[['BID', 'ASK'][i_idx_min]] = l_msg
                b_should_update = True
    return b_should_update, d_updates


def translate_trades_to_agent(row, my_book):
    '''
    Translate the instruction passed by an agent into trades messages to the
    environment.

    :param row: dict. the message from the agent
    :param my_book: LimitOrderBook object. The order book of an instrument
    :return: list. The messages to pass to the agent

    NOTE - *row* has the following form:
    row = {order_side, order_price, total_qty_order, instrument_symbol,
    agent_id}
    '''
    # recover the price levels of interest
    l_msg = []
    gen_bk = None
    s_side = row['order_side']
    if row['order_side'] == 'Sell Order':
        f_best_price = my_book.best_bid[0]
        f_max = f_best_price + 0.01
        f_min = row['order_price']
        gen_bk = my_book.book_bid.price_tree.item_slice(f_min,
                                                        f_max,
                                                        reverse=True)
    else:
        f_best_price = my_book.best_ask[0]
        f_max = row['order_price'] + 0.01
        f_min = f_best_price
        gen_bk = my_book.book_ask.price_tree.item_slice(f_min,
                                                        f_max,
                                                        reverse=False)
    # recover the price levels of interest
    b_stop = False
    b_row_from_agent = False
    i_qty = row['total_qty_order']
    if not gen_bk:
        return []
    for f_price, obj_price in gen_bk:
        if b_stop:
            break
        for idx_ord, obj_order in obj_price.order_tree.nsmallest(1000):
            order_aux = obj_order.d_msg

            # define how much should be traded
            i_qty_traded = order_aux['total_qty_order']  # remain
            i_qty_to_trade = min(i_qty, i_qty_traded)
            # check how many qty it still need to be traded
            i_qty -= i_qty_to_trade
            # define the status of the message
            if order_aux['total_qty_order'] <= i_qty_to_trade:
                s_status = 'Filled'
            else:
                s_status = 'Partially Filled'
            assert i_qty >= 0, 'Qty traded smaller than 0'
            # create the message
            i_new_qty_traded = order_aux['traded_qty_order'] + i_qty_to_trade
            # ==== [DEBUG] ====
            s_err = 'the total qty traded should be "lqt" total qty order'
            assert i_qty_traded <= order_aux['org_total_qty_order'], s_err
            # =================
            s_action = 'SELL'
            # if one  makes a trade at bid, it is a sell
            if s_side == 'Sell Order':
                s_action = 'BUY'
            s_action += '_crossed'
            # create a trade to fill that order
            d_new_msg = order_aux.copy()
            i_sec_order = my_book.i_sec_ask
            if order_aux['order_side'] == 'Buy Order':
                i_sec_order = my_book.i_sec_bid

            s_passive_action = order_aux['action']
            s_passive_action += '_crossed'

            i_org_qty = order_aux['org_total_qty_order']
            d_rtn = {'action': s_passive_action,
                     'agent_id': order_aux['agent_id'],
                     'agressor_indicator': 'Passive',
                     'execution_type': 'Trade',
                     'idx': order_aux['idx'],
                     'instrument_symbol': order_aux['instrument_symbol'],
                     'is_today': order_aux['is_today'],
                     'member': order_aux['member'],
                     'order_date': order_aux['order_date'],
                     'order_datetime_entry': my_book.s_time[:-7],
                     'order_id': order_aux['order_id'],
                     'order_price': order_aux['order_price'],
                     'order_side': order_aux['order_side'],
                     'order_status': s_status,
                     'org_total_qty_order': i_org_qty,
                     'priority_indicator': order_aux['priority_indicator'],
                     'priority_seconds': my_book.f_time,
                     'priority_time': my_book.s_time[11:],
                     'secondary_order_id': order_aux['secondary_order_id'],
                     'seq_order_number': order_aux['seq_order_number'],
                     'session_date': my_book.s_time[:10],
                     'total_qty_order': i_qty_traded - i_qty_to_trade,
                     'traded_qty_order': i_new_qty_traded,
                     'order_qty': i_qty_to_trade}

            # debug
            if not d_rtn['order_qty'] or d_rtn['order_qty'] < 0:
                # print 'translate_trades_to_agent'
                # print d_rtn
                # print i_qty_traded, i_qty_to_trade
                # raise NotImplementedError
                continue
            # end debug

            if 'neutrino_order' in order_aux:
                order = order_aux['neutrino_order']
                order.status = neutrino.FIXStatus.PENDING
                # order.current.price = order_aux['order_price']
                if not isinstance(order.current.qty, type(None)):
                    order.current.cumQty = min(
                        abs(i_new_qty_traded), order.current.qty)
                else:
                    order.current.cumQty = i_new_qty_traded
                if s_status == 'Partially Filled':
                    order.current.status = neutrino.FIXStatus.PARTIALLY_FILLED
                    order.current.isAlive = True
                elif s_status == 'Filled':
                    order.current.status = neutrino.FIXStatus.FILLED
                    order.current.isAlive = False
                d_rtn['neutrino_order'] = order

            l_msg.append(d_rtn.copy())
            # check the id of the agressive side

            # define the status of the agressor message
            if i_qty <= 0:
                s_status = 'Filled'
            else:
                s_status = 'Partially Filled'

            # create another message to update who took the action
            s_action = 'BUY'
            d_new_msg = my_book.d_bid.copy()
            # if one  makes a trade at bid, it is a sell
            if s_side == 'Sell Order':
                s_action = 'SELL'
                d_new_msg = my_book.d_ask.copy()
            s_action += '_crossed'
            my_book.i_my_order_id += 1
            s_sec_order_id = '{:015d}'.format(my_book.i_my_order_id)
            my_book.last_priority_id += 1
            i_priority_id = int(my_book.last_priority_id)
            my_book.i_last_order_id += 1  # NOTE: check that
            i_order_id = my_book.i_last_order_id

            s_sec_order_id = row['secondary_order_id']  # test
            i_priority_id = row['priority_indicator']
            i_order_id = row['order_id']

            d_rtn = {'action': s_action,
                     'agent_id': row['agent_id'],
                     'agressor_indicator': 'Agressor',
                     'execution_type': 'Trade',
                     'idx': '000000000000000',
                     'instrument_symbol': row['instrument_symbol'],
                     'is_today': row['is_today'],
                     'member': row['member'],
                     'order_date': row['order_date'],
                     'order_datetime_entry': my_book.s_time[:-7],
                     'order_id': i_order_id,  # i_priority_id,
                     'order_price': order_aux['order_price'],
                     'order_side': row['order_side'],
                     'order_status': s_status,
                     'org_total_qty_order': row['total_qty_order'],
                     'priority_indicator': i_priority_id,
                     'priority_seconds': my_book.f_time,
                     'priority_time': my_book.s_time[11:],
                     'secondary_order_id': s_sec_order_id,
                     'seq_order_number': s_sec_order_id,
                     'session_date': my_book.s_time[:10],
                     'total_qty_order': i_qty,
                     'traded_qty_order': row['total_qty_order'] - i_qty,
                     'order_qty': i_qty_to_trade}

            if 'neutrino_order' in row:
                b_row_from_agent = True
                order = row['neutrino_order']
                order.status = neutrino.FIXStatus.PENDING
                # order.current.price = order_aux['order_price']
                order.current.cumQty = min(
                    abs(i_new_qty_traded), order.current.qty)
                if s_status == 'Partially Filled':
                    order.current.status = neutrino.FIXStatus.PARTIALLY_FILLED
                    order.current.isAlive = True
                elif s_status == 'Filled':
                    order.current.status = neutrino.FIXStatus.FILLED
                    order.current.isAlive = False
                d_rtn['neutrino_order'] = order

            l_msg.append(d_rtn.copy())
            if i_qty <= 0:
                    b_stop = True
                    break
    if b_row_from_agent:
        l_msg = [row] + l_msg
    return l_msg


def translate_cancel_to_agent(agent, s_instr, s_action, s_side, i_n_to_cancel):
    '''
    Return a list of messages to cancel in the main order book, given the
    parameters passed

    :param agent: Agent Object.
    :param s_side: string. Side of the LOB
    :param s_action: string.
    :param s_instr: string. Instrument to cancel orders
    :param i_n_to_cancel: integer. Number of order to cancel
    '''
    l_msg = []
    orders_aux = agent.d_order_tree[s_instr][s_side]
    orders_func = orders_aux.nsmallest
    if s_side == 'ASK':
        orders_func = orders_aux.nlargest
    for f_key, d_aux in orders_func(i_n_to_cancel):
        d_rtn = d_aux.copy()
        d_rtn['order_status'] = 'Canceled'
        d_rtn['execution_type'] = 'Cancel'
        d_rtn['action'] = s_action
        l_msg.append(d_rtn.copy())
    return l_msg


def agent_env_neworder(order, my_book):
    '''
    Translate the order from an agent to a message to the limit order book

    :param agent: Agent object.
    :param order: Neutrino Order object
    '''
    if not order.next.price:
        return None
    # fill the current order
    order.current.price = order.next.price
    order.current.qty = order.next.qty
    if order.next.cumQty:
        order.current.cumQty = order.next.cumQty
    else:
        order.current.cumQty = 0
    order.current.timeInForce = order.next.timeInForce
    order.current.status = neutrino.FIXStatus.NEW
    order.current.isAlive = True
    order.status = neutrino.FIXStatus.PENDING
    # erase the next data
    order.next.price = None
    order.next.qty = None
    order.next.cumQty = None
    order.next.timeInForce = None
    # check the new IDs
    my_book.i_my_order_id += 1
    s_sec_order_id = '{:015d}'.format(my_book.i_my_order_id)
    my_book.last_priority_id += 1
    i_priority_id = int(my_book.last_priority_id)
    # fill msg to the simulator
    my_book.i_last_order_id += 1
    d_rtn = {'action': 'NEW',
             'agent_id': order.client,
             'neutrino_order': order,
             'agressor_indicator': 'Neutral',
             'execution_type': 'New',
             'idx': '000000000000000',
             'instrument_symbol': order.symbol,
             'is_today': True,
             'member': 9999,
             'order_date': '2016-03-29',
             'order_datetime_entry': my_book.s_time[:-7],
             'order_id': my_book.i_last_order_id,  # i_priority_id,
             'order_price': order.current.price,
             'order_side': SIDE[str(order.side)],
             'order_status': 'New',
             'org_total_qty_order': order.current.qty,
             'priority_indicator': i_priority_id,
             'priority_seconds': my_book.f_time,
             'priority_time': my_book.s_time[11:],
             'secondary_order_id': s_sec_order_id,
             'seq_order_number': s_sec_order_id,
             'session_date': my_book.s_time[:10],
             'total_qty_order': order.current.qty,
             'traded_qty_order': 0,
             'order_qty': order.current.qty}

    order.current.neutrinogymData = d_rtn
    order.current.secondaryOrderID = s_sec_order_id
    return d_rtn


def agent_env_cancellation(order, my_book):
    '''
    Translate the order from an agent to a message to the limit order book

    :param agent: Agent object.
    :param order: Neutrino Order object
    '''
    # fill the current order
    order.current.status = neutrino.FIXStatus.CANCELLED
    order.current.isAlive = False
    order.status = neutrino.FIXStatus.PENDING
    # fill msg to the simulator
    d_current = order.current.neutrinogymData
    d_current['order_status'] = 'Canceled'
    d_current['execution_type'] = 'Cancel'
    d_current['action'] = 'CANCEL'
    order.current.neutrinogymData = d_current

    return d_current


def agent_env_execution(order, my_book):
    raise NotImplementedError


def translate_to_agent(agent, s_action, my_book, f_spread=0.10, i_qty=None):
    '''
    Translate the action from an agent as a message to change the limit order
    book. The agent might have multiple orders, but just one by price. The
    action passed to the function is always related just to the best price of
    the agent. Also, the agent just can keep limit orders in the main
    instrument

    :param agent: Agent Object.
    :param s_action: string.
    :param my_book: LimitOrderBook object.
    :param *f_spread: float. Number of cents to include in the price. Also can
        be a LIST of separated spreads
    :param *i_qty: integer. Quantity to trade. If not defined, use default
    '''
    l_msg = []
    if not i_qty:
        i_qty = agent.order_size
    # filter prices if the quantity n the queue is 5 (the agent might be alone)
    t_best_bid = my_book.best_bid
    if t_best_bid[1] > agent.i_qty_to_be_alone:
        f_best_bid = t_best_bid[0]
    else:
        f_best_bid = t_best_bid[0] - 0.01
    t_best_ask = my_book.best_ask
    if t_best_ask[1] > agent.i_qty_to_be_alone:
        f_best_ask = t_best_ask[0]
    else:
        f_best_ask = t_best_ask[0] + 0.01
    # define an error to filter prices
    f_err_bid = +1e-6
    f_err_ask = -1e-6
    f_spread_bid = f_spread
    f_spread_ask = f_spread
    if isinstance(f_spread, list):
        f_spread_bid = f_spread[0]
        f_spread_ask = f_spread[1]
    if not s_action:
        f_err_bid = -1e-6
        f_err_ask = +1e-6
    elif s_action == 'BEST_BID':
        f_err_ask = +1e-6
    elif s_action == 'BEST_OFFER':
        f_err_bid = -1e-6
    # recover orders from the Bid side. Cancel everything that is better than
    # the price where the agent should have orders
    f_max = t_best_bid[0] + 0.01
    f_min = f_best_bid - f_spread_bid + f_err_bid
    orders_aux = agent.d_order_tree[my_book.s_instrument]['BID']
    for f_key, d_aux in orders_aux.item_slice(f_min, f_max, reverse=True):
        d_rtn = d_aux.copy()
        d_rtn['order_status'] = 'Canceled'
        d_rtn['execution_type'] = 'Cancel'
        d_rtn['action'] = s_action
        l_msg.append(d_rtn.copy())
    # apply the same rationale to the ask side
    f_min = t_best_ask[0] - 0.01
    f_max = f_best_ask + f_spread_ask + f_err_ask  # + 0.01
    orders_aux = agent.d_order_tree[my_book.s_instrument]['ASK']
    for f_key, d_aux in orders_aux.item_slice(f_min, f_max, reverse=False):
        d_rtn = d_aux.copy()
        d_rtn['order_status'] = 'Canceled'
        d_rtn['execution_type'] = 'Cancel'
        d_rtn['action'] = s_action
        l_msg.append(d_rtn.copy())

    # terminate if if should just cancel all the orders
    if not s_action:
        return l_msg

    # update when it has a limit order book message related to the bid side
    if s_action in ['BEST_BID', 'BEST_BOTH']:
        # set other variables
        s_symbol = my_book.s_instrument
        f_price = round((f_best_bid - f_spread_bid)*100)/100
        # check the new IDs
        my_book.i_my_order_id += 1
        s_sec_order_id = '{:015d}'.format(my_book.i_my_order_id)
        my_book.last_priority_id += 1
        i_priority_id = int(my_book.last_priority_id)
        orders_aux = agent.d_order_tree[my_book.s_instrument]['BID']
        # check if should change the price
        if not orders_aux.get(f_price):
            # include a new order
            my_book.i_last_order_id += 1
            d_rtn = {'action': s_action,
                     'agent_id': agent.i_id,
                     'agressor_indicator': 'Neutral',
                     'execution_type': 'New',
                     'idx': '000000000000000',
                     'instrument_symbol': s_symbol,
                     'is_today': True,
                     'member': 9999,
                     'order_date': '2016-03-29',
                     'order_datetime_entry': my_book.s_time[:-7],
                     'order_id': my_book.i_last_order_id,  # i_priority_id,
                     'order_price': f_price,
                     'order_side': 'Buy Order',
                     'order_status': 'New',
                     'org_total_qty_order': i_qty,
                     'priority_indicator': i_priority_id,
                     'priority_seconds': my_book.f_time,
                     'priority_time': my_book.s_time[11:],
                     'secondary_order_id': s_sec_order_id,
                     'seq_order_number': s_sec_order_id,
                     'session_date': my_book.s_time[:10],
                     'total_qty_order': i_qty,
                     'traded_qty_order': 0,
                     'order_qty': i_qty}
            l_msg.append(d_rtn.copy())
    # update when it has a limit order book message related to the ask side
    if s_action in ['BEST_OFFER', 'BEST_BOTH']:
        # set other variables
        s_symbol = my_book.s_instrument
        f_price = round((f_best_ask + f_spread_ask)*100)/100
        # check the new IDs
        my_book.i_my_order_id += 1
        s_sec_order_id = '{:015d}'.format(my_book.i_my_order_id)
        my_book.last_priority_id += 1
        i_priority_id = int(my_book.last_priority_id)
        orders_aux = agent.d_order_tree[my_book.s_instrument]['ASK']
        # check if should change the price
        if not orders_aux.get(f_price):
            # include a new order
            my_book.i_last_order_id += 1
            d_rtn = {'action': s_action,
                     'agent_id': agent.i_id,
                     'agressor_indicator': 'Neutral',
                     'execution_type': 'New',
                     'idx': '000000000000000',
                     'instrument_symbol': s_symbol,
                     'is_today': True,
                     'member': 9999,
                     'order_date': '2016-03-29',
                     'order_datetime_entry': my_book.s_time[:-7],
                     'order_id': my_book.i_last_order_id,
                     'order_price': f_price,
                     'order_side': 'Sell Order',
                     'order_status': 'New',
                     'org_total_qty_order': i_qty,
                     'priority_indicator': i_priority_id,
                     'priority_seconds': my_book.f_time,
                     'priority_time': my_book.s_time[11:],
                     'secondary_order_id': s_sec_order_id,
                     'seq_order_number': s_sec_order_id,
                     'session_date': my_book.s_time[:10],
                     'total_qty_order': i_qty,
                     'traded_qty_order': 0,
                     'order_qty': i_qty}
            l_msg.append(d_rtn.copy())
    return l_msg
