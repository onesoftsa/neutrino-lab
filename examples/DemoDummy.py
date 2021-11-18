import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
    import neutrinogym.neutrino as neutrino
else:
    from neutrino import *
    import neutrino

class DemoDummy(object):

    def initialize(self, symbols):
        print('Algorithm is ready to start')
        print('Requested symbols: ' + ','.join(symbols))
        for symbol in symbols:
            neutrino.market(self).add(symbol)

    def on_data(self, update):
        pass
