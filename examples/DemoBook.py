import platform

if '3.6' in platform.python_version():
    from neutrinogym.neutrino import *
else:
    from neutrino import *


class DemoBook(object):
    def initialize(self, symbols):
        print('Algorithm is ready to start')
        self.instruments = {}
        for symbol in symbols:
            self.instruments[symbol] = market(self).add(symbol)

    def print_book_entry(self, bid_entry, ask_entry):
        print(str(bid_entry.order_id) + ';' +
                str(bid_entry.virtual_md_id) + ';' +
                str(bid_entry.detail) + ';' +
                str(bid_entry.quantity) + ';' +
                str(bid_entry.price) + ' | ' +
                str(ask_entry.order_id) + ';' +
                str(ask_entry.virtual_md_id) + ';' +
                str(ask_entry.price) + ';' +
                str(ask_entry.quantity) + ';' +
                str(ask_entry.detail))

    def print_book_entries(self, book, entry_count = 5):
        if not (len(book.bid) >= entry_count and
            len(book.ask) >= entry_count):
            return
        print(book.name + ' ' + str(book.sequence) + ' ' + str(book.state))
        print('detail;qty;price | price;qty;detail')
        print(40*'-')
        for i in range(entry_count):
            self.print_book_entry(
                    book.bid[i],
                    book.ask[i])
        print()

    def on_data(self, update):
        if self.instruments[update.symbol].ready:
            reason_str = ','.join(str(r) for r in update.reason)
            print(str(update.symbol) + ' - ' + reason_str + ' ' + \
                str(self.instruments[update.symbol].min_order_qty) + ' ' + \
                str(self.instruments[update.symbol].price_increment))
            self.print_book_entries(self.instruments[update.symbol].book)
