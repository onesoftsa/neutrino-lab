import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
    import neutrinogym.neutrino as neutrino
else:
    from neutrino import *
    import neutrino
import time

class DemoCandles(object):
    def initialize(self, symbols):
        print('Algorithm is ready to start')
        self.printed = False
        self.symbol = symbols[0]
        self.instrument = market(self).add(self.symbol, trade_callback=self.on_trade, book_callback=None)
        self.bars = market(self).add_bar(self.symbol, bar_count=50, interval=5)
        self.sma = self.bars.add_sma(10, IndicatorSource.CLOSE)
        self.mom = self.bars.add_mom(10, IndicatorSource.CLOSE)
        self.samom = self.bars.add_samom(10, 5, IndicatorSource.CLOSE)
        self.stddev = self.bars.add_stddev(10, 10, IndicatorSource.CLOSE)
        self.adx = self.bars.add_adx(10)
        self.saadx = self.bars.add_saadx(10, 10)
        self.trange = self.bars.add_trange()
        self.satr = self.bars.add_satr(5)
        self.minus_di = self.bars.add_minus_di(10)
        self.plus_di = self.bars.add_plus_di(10)
        self.atr = self.bars.add_atr(10)
        self.ema = self.bars.add_ema(10, IndicatorSource.CLOSE)
        self.bbands = self.bars.add_bbands(10, 5, 5, IndicatorAverage.SMA)
        self.rsi = self.bars.add_rsi(bar_count=50, source=IndicatorSource.CLOSE)

        self.sar = self.bars.add_sar(acceleration=5, maximum=10)

        self.obv = self.bars.add_obv(source=IndicatorSource.CLOSE)

        self.stoch = self.bars.add_stoch(
            fast_k_ma_period=5,
            slow_k_ma_period=3,
            slow_k_ma_type=IndicatorAverage.SMA,
            slow_d_ma_period=3,
            slow_d_ma_type=IndicatorAverage.SMA)

        self.stochf = self.bars.add_stochf(
            fast_k_ma_period=3,
            fast_d_ma_period=5,
            fast_d_ma_type=IndicatorAverage.SMA)

        self.macd = self.bars.add_macd(
            fast_ma_type=IndicatorAverage.SMA,
            fast_ma_period=3,
            slow_ma_type=IndicatorAverage.SMA,
            slow_ma_period=5,
            signal_ma_type=IndicatorAverage.SMA,
            signal_ma_period=5)

        self.snapshot = False

    def print_last_candle(self):
        if len(self.bars.timestamps) == 0:
            return
        self.print_candle(self.bars.last_id)

    def print_candle(self, index):
        if len(self.bars.timestamps) == 0:
            return
        print('%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,'\
                '%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,'\
                '%.2f,%.2f,%d' % (
                    index,
                    self.bars.timestamps[index],
                    self.bars.open[index],
                    self.bars.high[index],
                    self.bars.low[index],
                    self.bars.close[index],
                    self.bars.quantity_buy[index],
                    self.bars.quantity_sell[index],
                    self.sma.values[0][index],
                    self.mom.values[0][index],
                    self.samom.values[0][index],
                    self.stddev.values[0][index],
                    self.adx.values[0][index],
                    self.saadx.values[0][index],
                    self.trange.values[0][index],
                    self.satr.values[0][index],
                    self.minus_di.values[0][index],
                    self.plus_di.values[0][index],
                    self.atr.values[0][index],
                    self.ema.values[0][index],
                    self.bbands.values[0][index],
                    self.bbands.values[1][index],
                    self.bbands.values[2][index],
                    self.rsi.values[0][index],
                    self.sar.values[0][index],
                    self.obv.values[0][index],
                    self.stoch.values[0][index],
                    self.stoch.values[1][index],
                    self.stochf.values[0][index],
                    self.stochf.values[1][index],
                    self.macd.values[0][index],
                    self.macd.values[1][index],
                    self.macd.values[2][index],
                    self.bars.num_trades[index],
                    ))

    def print_snapshot(self):
        print('id,open,high,low,close,qty_buy,qty_sell,sma,mom,samom,stddev,adx,saadx,trange,satr,'\
              'minus_di,plus_di,atr,ema,bbands1,bbands2,bbands3,rsi,sar,obv,stoch_slowk,stoch_slowd,'\
              'stochf_fastk,stochf_fastd,macd,macdsignal,macdhist,count')
        for index in range(len(self.bars.timestamps)):
            self.print_candle(index)

    def on_trade(self, update):
        if not self.bars.ready():
            return
        if not self.snapshot:
            self.print_snapshot()
            self.snapshot = True
            return
        reason_str = ','.join(str(r) for r in update.reason)
        print(str(update.symbol) + ' - ' + reason_str)
        self.print_last_candle()

    def finalize(self, reason):
        print('finalize: ' + str(reason))

    def set_parameters(self, config):
        pass
