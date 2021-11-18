import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
else:
    from neutrino import *

class DemoCallbacks(object):
    def initialize(self, symbols):
        self.symbol = symbols[0]
        print('Algorithm is ready to start with symbol ' + self.symbol)

        self.instrument = market(self).add(
            self.symbol,
            trade_buffer_size=10,
            trade_callback=None,
            book_callback=self.on_book)

    def on_book(self, update):
        print('on_book ' + update.symbol +
                ' bid_count: ' + str(update.bid_count) +
                ', ask_count: ' + str(update.ask_count) +
                ', state: ' + str(self.instrument.book.state))

    def on_trade(self, update):
        print('on_trade ' + update.symbol)

    def on_data(self, update):
        print('on_data ' + update.symbol)

