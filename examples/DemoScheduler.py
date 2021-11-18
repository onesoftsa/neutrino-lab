import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
    import neutrinogym.neutrino as neutrino
else:
    from neutrino import *
    import neutrino

class DemoScheduler(object):
    def initialize(self, symbols):
        print('Algorithm is ready to start')
        self.instruments = {}
        for symbol in symbols:
            self.instruments[symbol] = market(self).add(symbol)
        utils(self).at(self.at_function_1, 16, 27)
        utils(self).at(self.at_function_1, 16, 27)
        utils(self).every(self.every_function_1, 0.250)
        utils(self).every(self.every_function_1, 1.234)
        utils(self).every(self.every_function_2, 0.500)
        utils(self).every(self.every_function_2, 0.500)

        scheduled_functions = utils(self).get_functions()
        for scheduled_function in scheduled_functions:
            print(scheduled_function.function)
            print(str(scheduled_function.interval) + \
                    ' ' + str(scheduled_function.hour) + ':' + str(scheduled_function.minute))
            if (scheduled_function.interval == 0.25):
                utils(self).remove_function(scheduled_function)

    def at_function_1(self):
        print("at_function_1")

    def at_function_2(self):
        print("at_function_2")

    def every_function_1(self):
        print("every_function_1")

    def every_function_2(self):
        print("every_function_2")

    def on_data(self, update):
        pass

