#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Implement an Environment where all agents interact with. The environment is the
limit order book from interest rates future contracts

@author: ucaiado

Created on 11/07/2016
"""


from neutrinogym.qcore import Env


'''
Begin help functions
'''


'''
End help functions
'''


class LevelTwo(Env):
    '''
    Level Two Order book data Environment within which all agents operate. Use
    the PnL of the agent position as reward
    '''

    def __init__(self):
        '''
        Initialize an LevelTwo object
        '''
        super(LevelTwo, self).__init__()
