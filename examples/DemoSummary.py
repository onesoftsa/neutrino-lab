import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
    import neutrinogym.neutrino as neutrino
    # raise NotImplementedError('Summary line not supported in lab env...')
else:
    from neutrino import *
    import neutrino
import time

class DemoSummary(object):
    def initialize(self, symbols):
        print('Algorithm is ready to start')
        self.printed = False
        self.summaries = {}
        for symbol in symbols:
            self.summaries[symbol] = neutrino.market(self).add_summary(
                symbol=symbol, summary_callback=self.on_summary)

    def print_summary(self, summary):
        print(summary.symbol)
        print(summary.bid.price, summary.bid.quantity,
            summary.ask.price, summary.ask.quantity,
            summary.last_trade.status, summary.last_trade.price, summary.last_trade.quantity)
        print(summary.stats.trade_volume.quantity,
                summary.stats.high.price,
                summary.stats.low.price,
                summary.stats.vwap.price,
                summary.stats.opening.price,
                summary.stats.closing.price,
                summary.stats.theo.price,
                summary.stats.settlement.price,
                summary.stats.imbalance.quantity,
                summary.stats.tunnel.price,
                summary.stats.last.price)
        print(summary.tunnels.hard_limit.low_price,
                summary.tunnels.hard_limit.high_price,
                summary.tunnels.auction_limit.high_price,
                summary.tunnels.auction_limit.low_price,
                summary.tunnels.rejection_band.high_price,
                summary.tunnels.rejection_band.low_price,
                summary.tunnels.static_limit.high_price,
                summary.tunnels.static_limit.low_price)
        print(summary.status.status, summary.status.open_trade_time)

    def on_summary(self, update):
        self.print_summary(self.summaries[update.symbol])

    def finalize(self, reason):
        print('finalize: ' + str(reason))
