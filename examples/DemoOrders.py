import platform
import json

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
    import neutrinogym.neutrino as neutrino
else:
    from neutrino import *
    import neutrino

class DemoOrders(object):
    def initialize(self, symbols):
        print('Algorithm is ready to start',flush=True)
        self.instruments = {}
        self._params = {}
        self.symbol = symbols[0]
        self.instruments[self.symbol] = market(self).add(self.symbol)
        self.count = 0

    def on_data(self, update):
        if self.instruments[self.symbol].ready and self.count % 50 == 0:
            price = self.instruments[self.symbol].book.ask[0].price
            uid = oms(self).send_limit_order(self.symbol, Side.BID, price + 1, 5, TimeInForce.DAY)
        self.count += 1

    def order_update(self, order):
        print(order.status, flush=True)

    def set_parameters(self, config):
        print(config, flush=True)

    def get_parameters(self):
        return json.dumps(self._params)

    def finalize(self, reason):
        print('finalize: ' + str(reason), flush=True)

