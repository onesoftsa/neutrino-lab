#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
simulate Dummy startegy


@author: ucaiado

Created on 02/27/2018
"""
import importlib
import sys
import platform
import argparse
import textwrap
import json
import yaml
sys.path.append("../")

# define the required paths
s_platform = platform.system()
d_conf = yaml.safe_load(open('../neutrinogym/qcore/conf/conf_lab.yaml', 'r'))
s_path = d_conf['NEUTRINO_LAB'][s_platform]
s_root = d_conf['DATA_FOLDER'][s_platform]
s_logs = d_conf['LOGS'][s_platform]

# import the required neutrinogym related libs
sys.path.append(s_path)
neutrinogym = importlib.import_module('neutrinogym')
wrappers = importlib.import_module('neutrinogym.wrappers')
algos = importlib.import_module('neutrinogym.algos')
my_agent = importlib.import_module('examples')
agents_tests = importlib.import_module('simulate.agents_tests')


if __name__ == '__main__':
    s_txt = '''\
            Choose one agent to simulate from the list bellow
            --------------------------------------------
            - SendOrders
            - PrintTrades
            - PrintCandles
            - TestNotify
            - SchedulerTest
            '''
    obj_formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=obj_formatter,
                                     description=textwrap.dedent(s_txt))
    s_help = 'Choose an agentfrom the list'
    parser.add_argument('-a', '--agent', default='PrintCandles', type=str,
                        help=s_help)
    s_help = 'Choose a file to save the simulation output data'
    parser.add_argument('-f', '--file', default='None', type=str,
                        help=s_help)
    s_help = 'Number of episodes to run'
    parser.add_argument('-e', '--episodes', default=1, type=int,
                        help=s_help)
    s_help = 'Pop up  a window to render the PnL of the simulation'
    parser.add_argument('--viz', action='store_true', help=s_help)
    s_help = 'Save the PnL vizualization. Only used when viz is enabled'
    parser.add_argument('--save', action='store_true', help=s_help)
    s_help = 'Block the process to terminate.  Only used when viz is enabled'
    parser.add_argument('--block', action='store_true', help=s_help)
    args = parser.parse_args()

    # recover the arguments passed
    b_viz = args.viz
    b_save = args.save
    b_block = args.block
    i_episodes = args.episodes
    s_file = None
    if args.file != 'None':
        s_file = args.file

    d_implemented_agens = {'SendOrders': ('sendorders', my_agent.SendOrders),
                           'PrintTrades': ('printtrades', my_agent.PrintTrades),
                           'PrintCandles': ('printcandles', my_agent.PrintCandles),
                           'TestNotify': ('testnotify', my_agent.TestNotify),
                           'SchedulerTest': ('schltst', my_agent.SchedulerTest)}
    s_agent, agent_to_test = d_implemented_agens[args.agent]
    env = agents_tests.make_pnlenv()

    # define a list of commands to test
    l_commands = [json.dumps({'online': False})]
    l_commands = []

    # it is not been used by the Strategy yet
    d_params = {
        'symbols_conf': {'DI1F23': 25, 'DI1F25': 25},
        'open_pos': {'min_qty': 5,
                     'bid': True,
                     'ask': True}}

    l_setparams = [{s_agent: {'online': False, 'bid': False, 'ask': False}},
                   {s_agent: d_params},
                   # {s_agent: {'pos': {"DOLM18": {"P": 3704, "Q": -5}}}},
                   # {s_agent: {'pos': {"DOLM18": {"P": 3706, "Q": 0}}}},
                   # {s_agent: {'online': True, 'max_trades': None}},
                   {s_agent: {'online': True}}]

    # run the simulation
    env, agent, episodes = agents_tests.test_agent(MyAgent=agent_to_test,
                                                   env=env,
                                                   s_init='20190201',
                                                   s_end='201902010',
                                                   i_episodes=i_episodes,
                                                   s_root=s_root,
                                                   s_log=s_logs,
                                                   l_commands=l_commands,
                                                   l_setparams=l_setparams,
                                                   l_instruments=['DI1F23',
                                                                  'DI1F25'],
                                                   s_file=s_file,
                                                   b_plot=b_viz,
                                                   b_save=b_save,
                                                   b_block=b_block,
                                                   f_milis=100.,
                                                   b_randstart=False)
