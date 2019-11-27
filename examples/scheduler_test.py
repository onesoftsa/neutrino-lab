#!/usr/bin/python
# -*- coding: future_fstrings -*-
"""
...


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


def epoch2str(epoch):
    # from Fredy
    mlsec = "000"
    if str(epoch).find(".") >= 0:
            mlsec = repr(epoch).split('.')[1][:3]
    return time.strftime(
        '[%Y-%m-%d %H:%M:%S.{}]'.format(mlsec), time.localtime(epoch))

def get_hourminute(epoch, i_delta=0):
    # from Fredy
    obj = time.localtime(epoch + i_delta)
    return (obj.tm_hour, obj.tm_min)



'''
End help functions
'''


class SchedulerTest(object):
    def __init__(self):
        # initialize some variables
        self.i_count = 0
        self.i_count2 = 0
        self.i_keep_going = 1
        self._config = {}
        self._time_to_quit = False

    # new callbacks
    def initialize(self, symbols):
        # initialize new variables
        self.symbols = []
        self.symbols2 = [s for s in symbols]
        self.symbols3 = symbols
        self.already_removed = False
        self.my_symbol = symbols[0]
        i_hour, i_minute = get_hourminute(neutrino.utils.now(), 60*60 + 60*5)
        import pdb; pdb.set_trace()

        # NOTE: should be able to remove this line in prod
        neutrino.market.add(
            self.my_symbol, trade_callback=None, book_callback=None)

        # schedule functions
        self.my_every = neutrino.utils.every(self.on_event, interval=0.5)
        self.my_at = neutrino.utils.at(
            self.on_finishing, hour=i_hour, minute=i_minute)

    def on_finishing(self):
        s_msg = '\n%s on_finishing: new At' % epoch2str(neutrino.utils.now())
        print(s_msg)  # , flush=True)
        print('...removing all!!')  # , flush=True)
        for this_func in neutrino.utils.get_functions():
            # import pdb; pdb.set_trace()
            print(
                f'    removing function {this_func.function}: '
                f'interval={this_func.interval}, hour={this_func.hour}'
                f', minute={this_func.minute}')
            neutrino.utils.remove_function(this_func)

        print('\n!!WARNING: my function At should not show up above. Should print only below:')
        this_func = self.my_at
        print(f'    at function: {this_func.function}: '
              f'interval={this_func.interval}, hour={this_func.hour}'
              f', minute={this_func.minute}')

        print('\n...quitting!!')  # , flush=True)
        neutrino.utils.quit()
        return

    def on_event(self):
        # print every PRINT_EVERY counts
        self.i_count += 1
        if self.i_count % (PRINT_EVERY * self.i_keep_going) > 0:
            print('.', end="")  # , flush=True)
            return
        self.i_keep_going = 1
        print('\n%s on_event: new Every' % epoch2str(neutrino.utils.now()))


    def finalize(self, reason):
        self.i_count2 += 1
        s_t = epoch2str(neutrino.utils.now())
        print(f'{s_t}finalize {self.i_count, self.i_count2}: {str(reason)}')  # , flush=True)
        # neutrino.fx.quit()
