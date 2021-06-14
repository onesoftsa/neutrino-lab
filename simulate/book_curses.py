#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Visualize the orders of an agent in a LOB. Use this implementation as a starter
code to implement the visualizations you need. It requires that you use a
wrapper as the Monitor wrappers implemented in `wrappers` folder. It plot just
one book.


@author: ucaiado
based on: https://gist.github.com/claymcleod/b670285f334acd56ad1c

Created on 05/08/2021
"""

import time
import sys
import os
import socket
import json
import numpy as np
import curses


def draw_lob(stdscr):
    k = 0
    i_cursor_x = 0
    i_cursor_y = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Loop where k is the last character pressed
    while (k != ord('q')):
        # recover variables
        message, address = serverSocket.recvfrom(1024)
        d_data = json.loads(message)
        l_instruments = list(set(d_data['instruments']))
        d_count = {k: {
                'BID': len(d_data['agent_prices'][k]['B']),
                'ASK': len(d_data['agent_prices'][k]['A'])
            }
            for k in d_data['agent_prices'].keys()
        }

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if k == curses.KEY_DOWN:
            i_cursor_y = i_cursor_y + 1
        elif k == curses.KEY_UP:
            i_cursor_y = i_cursor_y - 1
        elif k == curses.KEY_RIGHT:
            i_cursor_x = i_cursor_x + 1
        elif k == curses.KEY_LEFT:
            i_cursor_x = i_cursor_x - 1

        i_cursor_x = max(0, i_cursor_x)
        i_cursor_x = min(width-1, i_cursor_x)

        i_cursor_y = max(0, i_cursor_y)
        i_cursor_y = min(height-1, i_cursor_y)

        # Declaration of strings
        s_title = f"{l_instruments[0]}"[:width-1]
        s_subtitle = f'{"qBid":>9}    {"Bid":^9}    {"Ask":^9}    {"qAsk":<9}'
        s_summary = ('%s, %s, %s' % (
            'PnL: R$ {:.01f}'.format(d_data['pnl']),
            'Pos: {:.0f}'.format(d_data['position']),
            'Num. agent prices: {:s}'.format(str(d_count)))
        )

        statusbarstr = "Press 'q' to exit | {}".format(s_summary)
        if k == 0:
            keystr = "No key press detected..."[:width-1]

        # Centering calculations
        i_start_x_title = int((width // 2) - (len(s_title) // 2) - len(s_title) % 2)
        i_start_x_subtitle = int(
            (width // 2) - (len(s_subtitle) // 2) - len(s_subtitle) % 2)


        i_start_y = int((height // 2) - 2)

        # Rendering some text
        s_time = f"  {d_data['time'][:-3]}"
        stdscr.addstr(0, 0, s_time, curses.color_pair(1))

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(
            height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

        # Turning on attributes for title
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        # Rendering title
        stdscr.addstr(i_start_y, i_start_x_title, s_title)

        # Turning off attributes for title
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)

        # Print rest of text
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(i_start_y + 2, i_start_x_subtitle, s_subtitle)
        stdscr.attroff(curses.A_BOLD)
        stdscr.addstr(i_start_y + 1, (width // 2) - 2, '-' * 4)

        # Print LOB
        d_agentp = d_data['agent_prices']
        s_cmm = l_instruments[0]
        b_test1 = s_cmm in d_agentp
        for ii, l_row in enumerate(d_data[s_cmm]):
            i_len_row = 9 * 4 + 4 * 3
            start_x_keystr = int(
                (width // 2) - (i_len_row // 2) - i_len_row % 2)
            # print qBID
            stdscr.addstr(
                i_start_y + ii + 3, start_x_keystr, f'{l_row[0]:>9}    ')
            # color LOB if agwnt hast an order on this price
            if b_test1 and float(l_row[1]) in d_agentp[s_cmm]['B']:
                stdscr.addstr(f'{l_row[1]:^9}    ', curses.color_pair(3))
            else:
                stdscr.addstr(f'{l_row[1]:^9}    ')
            if b_test1 and float(l_row[2]) in d_agentp[s_cmm]['A']:
                stdscr.addstr(f'{l_row[2]:^9}    ', curses.color_pair(3))
            else:
                stdscr.addstr(f'{l_row[2]:^9}    ')
            # print qASK
            stdscr.addstr(f'{l_row[3]:<9}    ')
        stdscr.move(i_cursor_y, i_cursor_x)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        stdscr.timeout(500)
        k = stdscr.getch()


def main():
    curses.wrapper(draw_lob)


if __name__ == '__main__':
    # initiate socket connection
    addr = ('127.0.0.1', 12000)

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(('', 12000))

    # initiate the animation
    message, address = serverSocket.recvfrom(1024)
    d_data = json.loads(message)

    # data structure of d_data:
    # {
    #     'DOLJ21': [
    #         ['25', '5691.50', '5692.50', '15'],
    #         ['35', '5691.00', '5693.00', '35'],
    #         ['25', '5690.50', '5693.50', '25'],
    #         ['60', '5690.00', '5694.00', '55'],
    #         ['35', '5689.50', '5694.50', '55']
    #     ],
    #     'agent_prices': {
    #         'DOLJ21': {
    #             'A': [5697.5, 5697.0, 5696.5, 5696.0, ],
    #             'B': [5685.5, 5686.0, 5686.5, 5687.0, 5687.5]
    #         }
    #     },
    #     'pnl': 7982.0,
    #     'position': 0,
    #     'time': '2021-03-02 11:35:08.6660000',
    #     'float_time': 1614692108,
    #     'instruments': ['DOLJ21', 'DOLJ21']
    # }

    main()
