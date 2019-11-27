#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Mimic some elements from Neutrino API to use in the unit tests

@author: ucaiado

Created on 09/21/2017
"""


def create_userdata(tokens, i_new_id=None, f_crrprice=None):
    '''
    return a dictionary to be stored in userdata attribute from a Order object

    :param tokens: dict. informations about the order
    :param i_id: int. the new/current ID of the order
    '''
    i_id = tokens.get('order_id')
    if not i_new_id:
        i_new_id = tokens.get('order_id')
    if not f_crrprice:
        f_crrprice = tokens.get('price')
    d_aux = {'p': f_crrprice, 'new_p': tokens.get('price'), 'id': i_id,
             'new_id': i_new_id}
    return d_aux


class TransactionFoo:
    '''
    A class that mimic the structure of a neutrino Transaction
    '''
    qty = 0
    price = 0.
    cumqty = 0.
    timeinforce = ''
    status = ''
    secondaryorderid = ''


class OderFoo:
    '''
    A class that mimic the structure of a neutrino Order
    '''

    def __init__(self, symbol, qty, price, userdata=None, side='BID'):
        '''
        '''
        self.order_id = ''
        self.current = TransactionFoo()
        self.current.qty = qty
        self.current.price = price
        self.userData = userdata
        self.b_is_alive = True
        self.b_ispending = True
        self.side = side
        self.symbol = symbol

        def is_alive(self): return self.b_is_alive

        def ispending(self): return self.b_ispending
