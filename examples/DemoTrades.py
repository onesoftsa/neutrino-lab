import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
    import neutrinogym.neutrino as neutrino
else:
    from neutrino import *
    import neutrino

class DemoTrades(object):
    def initialize(self, symbols):
        print('Algorithm is ready to start')
        self.trade_buffer_capacity = 5
        self.instrument = market(self).add(
            symbols[0], trade_buffer_size=self.trade_buffer_capacity);

    def print_trade_list_entry(self, trade_entry):
        print(
            str(trade_entry.trade_id) + ';' +
            str(trade_entry.status) + ';' +
            str(trade_entry.datetime) + ';' +
            str(trade_entry.quantity) + ';' +
            str(trade_entry.price))

    def print_trade_list_entries(self, i_trade_count=1):
        i_total_trades = len(self.instrument.trades)
        if not (i_total_trades >= self.trade_buffer_capacity):
            return
        print('trade_id;status;time;quantity;price')
        print(40*'-')

        i_start_iterating_on = max(0, i_total_trades - i_trade_count)
        for ii in range(i_start_iterating_on, i_total_trades, 1):
            self.print_trade_list_entry(self.instrument.trades[ii])

        print()

    def on_data(self, update):
        if not self.instrument.ready():
            print('Trades not ready yet')
            return
        if not (UpdateReason.TRADES in update.reason):
            return
        reason_str = ','.join(str(r) for r in update.reason)

        print(str(update.symbol) + ' - ' + reason_str)
        self.print_trade_list_entries(update.trade_count)
