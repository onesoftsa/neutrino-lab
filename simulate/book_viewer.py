#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Visualize the orders of an agent in a LOB. Use this implementation as a starter
code to implement the visualizations you need. It requires that you use a
wrapper as the Monitor wrappers implemented in `wrappers` folder.


@author: ucaiado

Created on 01/11/2018
"""

import time
import socket
import pickle
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

import numpy
from mpl_toolkits.axes_grid1 import host_subplot
import matplotlib.animation as animation

'''
Begin help functions
'''

text_style = dict(horizontalalignment='right', verticalalignment='center',
                  fontsize=14, fontdict={'family': 'sans-serif'})

header_style = dict(horizontalalignment='right', verticalalignment='center',
                    fontsize=15, fontdict={'family': 'sans-serif'},
                    color='black', weight='bold')

time_style = dict(horizontalalignment='center', verticalalignment='center',
                  fontsize=17, fontdict={'family': 'sans-serif'},
                  color='black', weight='bold')
info_style = dict(horizontalalignment='left', verticalalignment='center',
                  fontsize=13, fontdict={'family': 'sans-serif'})

'''
End help functions
'''


def img_init(fig, l_instr, d_data):
    '''
    Initialize a matplotlib image to simulate the order books used by an agent

    :param l_instr: list. List of the instruments to be monitored
    :param d_data: dict. Data passed by the monitoring Wrapper
    '''
    # initialize the subplots in the figure
    i_mcol = min(6, max(len(l_instr) * 2, 4))
    i_mrow = int(np.ceil(len(l_instr) * 2 / 6.))

    ax_time = plt.subplot2grid((i_mrow*2+1, i_mcol), (0, 0), colspan=i_mcol-2,
                               rowspan=1)
    ax_time.axis('off')
    t0 = ax_time.text(.5, 0.5, str(datetime.now())[:-3], **time_style)

    ax_summary = plt.subplot2grid((i_mrow*2+1, i_mcol), (0, i_mcol-2),
                                  colspan=2, rowspan=1)
    f_pnl = 0.
    f_pos = 0.
    f_delta = 0.
    f_tot = 0
    ax_summary.axis('off')
    t1 = ax_summary.text(0.2, 0.96, 'PnL: R$ {:.01f}'.format(f_pnl),
                         **info_style)
    t2 = ax_summary.text(0.2, 0.64, 'Total pos: {:.0f}'.format(f_pos),
                         **info_style)
    t3 = ax_summary.text(0.2, 0.32, 'PnL from Pos: {:.01f}'.format(f_delta),
                         **info_style)
    t4 = ax_summary.text(0.2, 0., 'Total traded: {:.0f}'.format(f_tot),
                         **info_style)

    l_ax = []

    i_charts = len(l_instr)
    i_count = 0
    for i_row in range(1, i_mrow*2+1, 2):
        for i_col in range(0, i_mcol, 2):
            i_count += 1
            l_ax.append(plt.subplot2grid((i_mrow*2+1, i_mcol), (i_row, i_col),
                                         colspan=2, rowspan=2))
            if i_count >= i_charts:
                break
    l_instr = list(l_instr)
    d_ax = dict(zip(sorted(l_instr), l_ax))
    # fill each subplot with a book
    d_obj = {}
    d_obj['time'] = {'ax': ax_time, 'txt': t0}
    d_obj['summary'] = {'ax': ax_summary, 'pnl': t1, 'pos': t2, 'pos_pnl': t3,
                        'tot': t4}
    for s_cmm in l_instr:
        d_obj[s_cmm] = {'ax': d_ax[s_cmm]}
        ax = d_ax[s_cmm]
        l_col = ['qBid', 'Bid', 'Ask', 'qAsk']
        df_book = pd.DataFrame(d_data[s_cmm], columns=l_col)

        ax.axis('off')
        ax.set_title(s_cmm + '\n', fontsize=16)
        i_row, i_col = df_book.shape
        l_txt_format = ['{}', '{}', '{}', '{}']

        ax.text(0.1, 1.00, 'qBid', **header_style)
        ax.text(0.35, 1.00, 'Bid', **header_style)
        ax.text(0.6, 1.00, 'Ask', **header_style)
        ax.text(0.85, 1.00, 'qAsk', **header_style)

        d_obj[s_cmm] = {'ax': d_ax[s_cmm],
                        'qBid': {1: None, 2: None, 3: None, 4: None, 5: None},
                        'Bid': {1: None, 2: None, 3: None, 4: None, 5: None},
                        'Ask': {1: None, 2: None, 3: None, 4: None, 5: None},
                        'qAsk': {1: None, 2: None, 3: None, 4: None, 5: None}}
        for i in range(i_row):

            # qBid
            s_txt = '{}'.format(df_book.iloc[i, 0])
            d_obj[s_cmm]['qBid'][i] = ax.text(0.1, 0.80 - i * 0.22, s_txt,
                                              **text_style)

            # Bid / Ask
            s_txt1 = '{}'.format(df_book.iloc[i, 1])
            s_txt2 = '{}'.format(df_book.iloc[i, 2])
            d_obj[s_cmm]['Bid'][i] = ax.text(0.35, 0.80 - i * 0.22, s_txt1,
                                             **text_style)
            d_obj[s_cmm]['Ask'][i] = ax.text(0.6, 0.80 - i * 0.22, s_txt2,
                                             **text_style)

            # qAsk
            s_txt = '{}'.format(df_book.iloc[i, 3])
            d_obj[s_cmm]['qAsk'][i] = ax.text(0.85, 0.80 - i * 0.22, s_txt,
                                              **text_style)

    # fig.tight_layout()
    fig.set_tight_layout(True)
    fig.subplots_adjust(bottom=0.01)
    return d_obj


def img_update(i, d_obj, serverSocket, l_instr):
    '''
    Update the MatplobLib image created by img_init to produce an order book
    vizualization

    :param l_instr: list. List of the instruments to be monitored
    :param d_data: dict. Data passed by the monitoring Wrapper
    '''

    message, address = serverSocket.recvfrom(1024)
    # d_data = pickle.loads(message)
    d_data = json.loads(message)

    f_pnl = 0.
    f_pos = 0.
    f_tot = 0.
    f_tot += 0.
    f_delta = 0.
    d_agent_prices = d_data['agent_prices']
    try:

        f_pnl = d_data['pnl']
        f_pos = d_data['position']

        d_obj['time']['txt'].set_text(d_data['time'][:-3])
        d_obj['summary']['pnl'].set_text('PnL: R$ {:.01f}'.format(f_pnl))
        d_obj['summary']['pos'].set_text('Total pos: {:.0f}'.format(f_pos))
        s_txt = 'PnL from Pos: {:.01f}'
        d_obj['summary']['pos_pnl'].set_text(s_txt.format(f_delta))
        d_obj['summary']['tot'].set_text('Total traded: {:.0f}'.format(f_tot))
    except TypeError:
        pass
    for s_cmm in l_instr:
        l_col = ['qBid', 'Bid', 'Ask', 'qAsk']
        df_book = pd.DataFrame(d_data[s_cmm], columns=l_col)
        for i in range(df_book.shape[0]):
            # qBid
            s_txt = '{}'.format(df_book.iloc[i, 0])
            d_obj[s_cmm]['qBid'][i].set_text(s_txt)
            # Bid
            s_txt1 = '{}'.format(df_book.iloc[i, 1])
            d_obj[s_cmm]['Bid'][i].set_text(s_txt1)
            b_test1 = s_cmm in d_agent_prices
            if b_test1 and float(df_book.iloc[i, 1]) in d_agent_prices[s_cmm]:
                d_obj[s_cmm]['Bid'][i].set_bbox(dict(facecolor='gray',
                                                     alpha=0.5,
                                                     edgecolor='none'))
            else:
                d_obj[s_cmm]['Bid'][i].set_bbox(None)
            # Ask
            s_txt2 = '{}'.format(df_book.iloc[i, 2])
            d_obj[s_cmm]['Ask'][i].set_text(s_txt2)
            if b_test1 and float(df_book.iloc[i, 2]) in d_agent_prices[s_cmm]:
                d_obj[s_cmm]['Ask'][i].set_bbox(dict(facecolor='gray',
                                                     alpha=0.5,
                                                     edgecolor='none'))
            else:
                d_obj[s_cmm]['Ask'][i].set_bbox(None)

            # qAsk
            s_txt = '{}'.format(df_book.iloc[i, 3])
            d_obj[s_cmm]['qAsk'][i].set_text(s_txt)

    return d_obj


if __name__ == '__main__':
    # initiate socket connection
    addr = ('127.0.0.1', 12000)

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(('', 12000))

    # initiate the animation
    message, address = serverSocket.recvfrom(1024)

    # d_data = pickle.loads(message)
    d_data = json.loads(message)

    # set the list of instruments used in conf file
    INSTRUMENTS = d_data['instruments']

    t_figsize = (8, 4)
    if len(INSTRUMENTS) > 3:
        t_figsize = (11, 8)
    fig_book = plt.figure(figsize=t_figsize)
    d_img_book = img_init(fig_book, INSTRUMENTS, d_data)

    simulation = animation.FuncAnimation(fig_book, img_update, blit=False,
                                         frames=None, interval=1, repeat=False,
                                         fargs=(d_img_book, serverSocket,
                                                INSTRUMENTS))

    # Uncomment the next line if you want to save the animation
    # simulation.save(filename='sim.html',fps=30,dpi=300)

    plt.show()
