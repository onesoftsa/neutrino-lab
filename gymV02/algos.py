"""
...

@author: ucaiado

Created on 07/06/2018
"""

from .qcore import (Agent, Env, get_begin_time, orders, books, candles,
                    SubscrType, CandleIntervals, CommandHandler, neutrino_now,
                    include_to_this_order, OrderHandler, EnvWrapper,
                    AgentWrapper)

Strategy = Agent

__version__ = 'v0.2.2.6.2:4f6e078'

__all__ = ['Agent', 'Strategy', 'get_begin_time', 'orders', 'books', 'Env',
           'SubscrType', 'CommandHandler', 'neutrino_now', 'OrderHandler',
           'include_to_this_order', 'EnvWrapper', 'AgentWrapper']
