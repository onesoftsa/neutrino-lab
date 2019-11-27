#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Handle order bookkepping of the agent


@author: ucaiado

Created on 09/21/2017
'''


'''
Begin help functions
'''


SIDE_MAP = {'BID': {'Q': 'qBid', 'V': 'Bid'}, 'ASK': {'Q': 'qAsk', 'V': 'Ask'}}
OTHER_SIDE = {'BID': 'ASK', 'ASK': 'BID'}
MAP_TYPE = {'M': 1, 'PM': -1, 'E': -1, 'N': 1, 'RC': -1}

'''
End help functions
'''


def priority_changed(order, d_tokens):
    '''
    Check if the priority of an existing order has changed

    :param order: neutrino Order. The current order got from _order
    :param d_tokens: dict. Order parameters.
    '''
    # check if should include a new order ID to this order
    d_tokens['new_id'] = d_tokens.get('order_id')
    b_1 = float(d_tokens.get('qty')) > order.current.qty
    b_2 = float(d_tokens.get('price')) != order.current.price
    return (b_1 or b_2)


def update_order_ctrls(order, d_orders, d_prices, s_state=None):
    '''
    Update the order map and the price map updated given the order passed

    :param order: neutrino Order. The current order got from _order
    :param d_orders: dict. The agent _orders attribute. It is the order map
    :param d_orders: dict. The agent _prices attribute. It is the price map
    '''
    if not s_state:
        s_state = str(order.current.status)
    d_usrdata = order.userData
    # d_usrdata = {a: b for a, b in iter(order.userData.items())}
    s_side = str(order.side)
    s_symbol = str(order.symbol)
    if s_state in ['NEW', 'REPLACED', 'PENDING']:
        # UPDATE 10-30-2017: PENDING ensure the agent is tracking any price
        if d_usrdata['new_id'] != d_usrdata['id']:
            # print 'update_order_ctrls(): state ', s_state
            # exclude the old ID
            # print 'bko.update_order_ctrls(): pop 1 - id: ', d_usrdata['id']
            d_orders.pop(d_usrdata['id'])
            f_price = d_usrdata['p']
            i_id = d_usrdata['id']
            d_prices[s_side][f_price].remove(i_id)
            if len(d_prices[s_side][f_price]) == 0:
                del d_prices[s_side][f_price]

        # include the new id
        # print 'update_order_ctrls(): update userData '
        order.userData['id'] = d_usrdata['new_id']
        d_orders[d_usrdata['id']] = order
        f_price = d_usrdata['new_p']

        # debug
        # print d_prices, d_usrdata
        # TODO: debug this
        f_price_old = d_usrdata['p']
        if f_price != f_price_old and f_price_old in d_prices[s_side]:
            d_prices[s_side][f_price_old].discard(d_usrdata['id'])
        ####

        order.userData['p'] = d_usrdata['new_p']
        if f_price_old in d_prices[s_side]:
            if not d_prices[s_side][f_price_old]:
                del d_prices[s_side][f_price_old]

        try:
            d_prices[s_side][f_price].add(d_usrdata['id'])
        except KeyError:
            d_prices[s_side][f_price] = set()
            d_prices[s_side][f_price].add(d_usrdata['id'])
        # order.userData['p'] = d_usrdata['new_p']
        # NOTE: REJECTED is only related to new orders
    elif s_state in ['CANCELLED', 'FILLED', 'REJECTED']:
        # exclude the old ID
        try:
            d_orders.pop(d_usrdata['id'])
            f_price = d_usrdata['p']
            d_prices[s_side][f_price].remove(d_usrdata['id'])
            if len(d_prices[s_side][f_price]) == 0:
                del d_prices[s_side][f_price]

        except KeyError:
            # TODO: investigate where is the error in simulator
            # look for the old ID
            i_old_id = None
            for i_key, ord_aux in iter(d_orders.items()):
                if ord_aux.userData['id'] == d_usrdata['id']:
                    i_old_id = i_key
                    break
            # use the old id
            if i_old_id:
                s_msg = 'update_order_ctrls(): Did not find the ID {}, '
                s_msg += 'however found {}'
                print(s_msg.format(d_usrdata['id'], ord_aux))
                d_orders.pop(i_old_id)
                for f_p in [d_usrdata['p'], ord_aux.userData['p']]:
                    if f_p in d_prices[s_side]:
                        if i_old_id in d_prices[s_side][f_p]:
                            d_prices[s_side][f_p].remove(i_old_id)
                        if len(d_prices[s_side][f_p]) == 0:
                            del d_prices[s_side][f_p]


def update_position(s_instr, s_side, lastpx, lastqty, d_positions, d_open_pos):
    '''
    Update the agent's position controls

    :param s_instr: string. instrument update
    :param s_side: string. BID or ASK
    :pram lastpx: float. Last prices traded
    :pram lastqty: integer.Last qty traded
    :param d_positions: dictionary. position in each instrument
    :param d_open_pos: dictionary. open positions in each ionstrument
    '''
    # update daily position
    i_last_pos = d_positions['qBid'] - d_positions['qAsk']
    d_positions[SIDE_MAP[s_side]['Q']] += lastqty
    d_positions[SIDE_MAP[s_side]['V']] += (lastqty*lastpx)
    i_curr_pos = d_positions['qBid'] - d_positions['qAsk']
    # update current position
    f_qty = lastqty
    f_qty *= -1 if s_side == 'ASK' else 1
    if i_curr_pos == 0:
        d_open_pos[OTHER_SIDE[s_side]] = []
        d_open_pos[s_side] = []
    elif i_curr_pos != 0 and i_last_pos == 0:
        d_open_pos[s_side].append((lastqty, lastpx))
    elif (i_last_pos < 0 and f_qty < 0) or ((i_last_pos > 0 and f_qty > 0)):
        d_open_pos[s_side].append((lastqty, lastpx))
    elif (i_last_pos < 0 and f_qty > 0) or ((i_last_pos > 0 and f_qty < 0)):
        # close out the opened position and open a new one in oposite side
        if (i_curr_pos/i_last_pos) < 0:
            d_open_pos[OTHER_SIDE[s_side]] = []
            d_open_pos[s_side] = [(abs(i_curr_pos), lastpx)]
        # close out opened positions
        else:
            f_qty_to_match = abs(f_qty)
            l_aux = []
            # l_avlb = d_open_pos[OTHER_SIDE[s_side]]  # FIFO
            l_avlb = d_open_pos[OTHER_SIDE[s_side]][::-1]  # LIFO
            for i_thisQ, f_thisP in l_avlb:
                if f_qty_to_match == 0:
                    l_aux.append((i_thisQ, f_thisP))
                elif i_thisQ <= f_qty_to_match:
                    f_qty_to_match -= i_thisQ
                elif i_thisQ > f_qty_to_match:
                    i_thisQ -= f_qty_to_match
                    f_qty_to_match = 0
                    l_aux.append((i_thisQ, f_thisP))
            d_open_pos[OTHER_SIDE[s_side]] = l_aux


def account_active_qty(d_active_qty, s_symbol, s_side, s_type, i_qty, i_len=100):
    '''
    Bookkeeping the active orders in the order book

    :param d_active_qty: dictionary. The total active qty by symbol and side
    :param s_symbol: string. Instrument of the update
    :param s_side: string. Side of the update
    :param s_type: string. source of change in _active_qty attribute. Can be
        PM (pre-modification), M (modification), N (New), E (Execution) and
        CR (Cancel or Rejection)
    :param i_qty: int. the qty related to this update
    '''
    d_active_qty[s_side] += i_qty * MAP_TYPE[s_type]
    d_active_qty[s_side] = max(0, d_active_qty[s_side])
    if not i_len or d_active_qty[s_side] < 0:
        d_active_qty[s_side] = 0

