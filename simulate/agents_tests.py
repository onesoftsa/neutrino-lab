#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Example of customized environment and agent wrappers

@author: ucaiado

Created on 02/21/2018
"""

import json
import pprint
from tqdm import tqdm
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.lines import Line2D
import neutrinogym


class PnLEnv(neutrinogym.EnvWrapper):

    _dv01 = {'DI1F21': 103.91 * 100./2,
             'DI1F23': 144.07 * 100./2,
             'DI1F25': 166.07 * 100./2,
             'DI1F27': 175.14 * 100./2,
             'DOLH19': 50.}

    def __init__(self, env):
        super(PnLEnv, self).__init__(env)
        self.d_trial_data['agents_pnl'] = {}
        self.d_trial_data['hist_pnl'] = {}
        self.env.get_reward = self.get_reward
        self._last_time_pnl = 0.
        self._new_infos = False

    def get_reward(self, actions):
        '''
        Return the reward based on the current state of the market and position
        accumulated by the agent

        :param actions: Action object.
        '''
        # return 0
        # NOTE:  this procedure adds 10% more time to the simulation
        agent = actions.owner
        if agent.i_id not in self.d_trial_data['agents_pnl']:
            self.d_trial_data['agents_pnl'][agent.i_id] = 0.
            self.d_trial_data['hist_pnl'][agent.i_id] = []
        f_last_pnl = self.d_trial_data['agents_pnl'][agent.i_id]
        f_curr_pnl = 0.
        d_position = self.d_trial_data['agents_positions'][agent.i_id]
        # do calculations
        for instr in agent._instr_stack.values():
            # check the qty position
            s_asset = instr.symbol_name
            i_qty = instr._position['qBid']
            i_qty -= instr._position['qAsk']
            i_qty += d_position[s_asset]['qBid']
            i_qty -= d_position[s_asset]['qAsk']
            # check the volume
            f_vol = instr._position['Bid']
            f_vol -= instr._position['Ask']
            f_vol += d_position[s_asset]['Bid']
            f_vol -= d_position[s_asset]['Ask']
            f_vol *= -1
            if i_qty == 0:
                f_pnl = (f_vol) * self._dv01[s_asset]
                f_curr_pnl += f_pnl
                continue
            # calcule the pnl
            my_book = self.get_order_book(s_asset)
            (f_bid, _) = my_book.best_bid
            (f_ask, _) = my_book.best_ask
            f_mid = (f_bid + f_ask)/2.
            f_pnl = (f_vol + i_qty * f_mid) * self._dv01[s_asset]
            f_curr_pnl += f_pnl

        self.d_trial_data['agents_pnl'][agent.i_id] = f_curr_pnl
        f_time = neutrinogym.neutrino.fx.now()
        if f_time - self._last_time_pnl > 300.:
            self._new_infos = True
            s_time = neutrinogym.neutrino.fx.now(True)
            d_aux = {'time': s_time, 'pnl': f_curr_pnl}
            self._last_time_pnl = f_time
            self.d_trial_data['hist_pnl'][agent.i_id].append(d_aux)
        elif f_time < self._last_time_pnl:
            self._last_time_pnl = f_time

        agent._env_pnl = f_curr_pnl
        return f_curr_pnl - f_last_pnl


def get_order_book(book, func):
    '''
    Return a dataframe representing the order book passed

    :param book. neutrino Book. Limit order book of a specific instrument
    :param func. neutrino function. Function byprice from API
    '''
    i_depth = 5
    l_rtn = [[0, 0., 0., 0] for x in range(i_depth)]
    # old
    # bid = func(book.bid(), i_depth)
    # ask = func(book.ask(), i_depth)
    bid = func(book.bid, i_depth)
    ask = func(book.ask, i_depth)
    for x in range(i_depth):
        try:
            if bid and abs(bid[x].price) > 10e-4 and abs(bid[x].price) < 10**8:
                l_rtn[x][0] = '{:0.0f}'.format(bid[x].quantity)
                l_rtn[x][1] = '{:0.2f}'.format(bid[x].price)
        except IndexError:
            pass
        try:
            if ask and abs(ask[x].price) > 10e-4 and abs(ask[x].price) < 10**8:
                l_rtn[x][2] = '{:0.2f}'.format(ask[x].price)
                l_rtn[x][3] = '{:0.0f}'.format(ask[x].quantity)
        except IndexError:
            pass
    return l_rtn


class MyMonitor(neutrinogym.wrappers.Monitor):
    '''
    '''
    def __init__(self, agent):
        '''
        Initiate a Tester instance. Save all parameters as attributes

        :param agent: Agent object.
        '''
        super(MyMonitor, self).__init__(agent)
        self._baseagent += '_MyMonitor'
        self.last_id = 0
        self._env_pnl = 0.
        self.last_json = {}

    def get_data_to_render(self):
        '''
        '''
        d_to_pickle = {}
        # recover books
        for s_cmm in self._instr_from_conf:
            df_book = get_order_book(neutrinogym.neutrino.fx.book(s_cmm),
                                     neutrinogym.neutrino.byPrice)
            d_to_pickle[s_cmm] = df_book
        # recover agent prices
        d_agent_prices = {}
        # try:
        for instr in self._instr_stack.values():
            l_aux = [x for x in instr._prices['ASK'].keys()]
            l_aux += [x for x in instr._prices['BID'].keys()]
            d_agent_prices[instr.symbol_name] = l_aux
        # except (KeyError, AttributeError) as e:
        #     pass
        # print d_agent_prices
        d_to_pickle['agent_prices'] = d_agent_prices

        # fill other information
        d_to_pickle['pnl'] = self._env_pnl
        f_pos = 0
        for instr in iter(self.agent._instr_stack.values()):
            f_pos += instr.get_position()
        d_to_pickle['position'] = f_pos
        d_to_pickle['time'] = neutrinogym.neutrino.fx.now(True)
        d_to_pickle['float_time'] = int(neutrinogym.neutrino.fx.now())
        d_to_pickle['instruments'] = self._instr_from_conf
        s_serialized = json.dumps(d_to_pickle)
        self.last_json = s_serialized
        return s_serialized


def make_pnlenv():
    env = neutrinogym.make('LevelTwo')
    env = PnLEnv(env)
    return env


def get_current_sha():
    try:
        import git
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        return sha[:7]
    except:
        return ''


def mypause(interval):
    backend = plt.rcParams['backend']
    if backend in matplotlib.rcsetup.interactive_bk:
        figManager = matplotlib._pylab_helpers.Gcf.get_active()
        if figManager is not None:
            canvas = figManager.canvas
            if canvas.figure.stale:
                canvas.draw()
            canvas.start_event_loop(interval)
            return


def setup_simulation(agent, l_instrconf=None, i_id=None, brain=None):
    if hasattr(agent, 'setup_simulation'):
        agent.setup_simulation(
            l_instr_from_conf=l_instrconf, i_agentid=i_id, brain=brain)
        return
    agent.i_id = i_id
    agent._instr_from_conf = l_instrconf
    # set RL agents parameters
    agent.brain = brain


def test_agent(MyAgent, env, s_root, s_log, i_episodes=5, s_init='20180501',
               s_end='20180503', l_commands=[], l_setparams=[],
               l_instruments=[], b_just_once=True, s_file=None, b_plot=True,
               b_save=True, b_block=False, f_milis=100., b_randstart=True):
    # start an environment and an agent
    agent = MyAgent()
    if l_instruments:
        i_id = getattr(agent, 'i_id', 11)
        brain = getattr(agent, 'brain', None)
        setup_simulation(
            agent, l_instrconf=l_instruments, i_id=i_id, brain=brain)
    l_instruments = agent._instr_from_conf
    agent = MyMonitor(agent)

    # set dates. Make sure that the `neutrinogym.conf` file is set
    episodes_info = env.setParameters(init=s_init,
                                      end=s_end,
                                      datafolder=s_root,
                                      starttime='09:30:00',
                                      endtime='15:30:00',
                                      logfolder=s_log,
                                      instruments=l_instruments,
                                      f_milis=f_milis,
                                      b_randstart=b_randstart)

    # run a simulation using all order book order book data
    if isinstance(i_episodes, type(None)):
        i_episodes = episodes_info.total
    print('\n###########################################')
    print('Start simulation of %i episode(s)' % i_episodes)
    print(' > gym version: %s' % neutrinogym.algos.__version__)
    s_sha = get_current_sha()
    if s_sha:
        env.agent_sha = s_sha
        print(' > repo hex: %s' % s_sha)

    if b_plot:
        plt.style.use('ggplot')
        f, ax = plt.subplots(1, 1)
        ax.set_title('Live PnL', fontsize=16)
        ax.set_ylabel('PnL')
        ax.set_xlabel('timeidx')
        obj_line = Line2D([], [], color='#1dcaff')
        _ = ax.add_line(obj_line)
        f.show()

    for i_episode in tqdm(range(i_episodes)):
        print('\n###########################################\n')
        observation = env.reset()
        env.resetAgent(agent, hold_pos=True)

        # correct parameters and dump them
        l_setparams2 = [json.dumps(x) for x in l_setparams]

        if b_just_once and i_episode == 0:
            env.set_agent_params(agent, 'command', l_commands)
            env.set_agent_params(agent, 'parameters', l_setparams2)
        elif not b_just_once:
            env.set_agent_params(agent, 'command', l_commands)
            env.set_agent_params(agent, 'parameters', l_setparams2)

        # print current parameters
        print('processGetParameters output:')
        env.get_agent_params(agent)
        pprint.pprint(json.loads(env.get_agent_params(agent)))
        print('\n')

        while True:
            agent.render()
            actions = env.callBack(agent, observation)
            observation, reward, done, info = env.step(actions)
            # plot PnL
            if b_plot and env._new_infos:
                env._new_infos = False
                df = pd.DataFrame(env.d_trial_data['hist_pnl'][11])
                obj_line.set_data(df.index, df.pnl.values)
                ax.relim()
                ax.autoscale_view()
                mypause(0.1)

            # check if the environment is done
            if done:
                agent.flush(env)
                f_pnl = env.d_trial_data['hist_pnl'][11][-1]['pnl']
                print('\n###########################################')
                s_msg = 'Episode {} finished.\nAcummulated PnL {}'
                s_msg = s_msg.format(episodes_info.getDate(i_episode), f_pnl)
                print(s_msg)
                break

    if s_file:
        print('Saving results at {}'.format(s_log + 'log/' + s_file))
        df = pd.DataFrame(env.d_trial_data['hist_pnl'][11])
        df.to_hdf(s_log + 'log/' + s_file, 'w')

    env.close()
    print('###########################################\n')
    if b_plot and b_save:
        f.savefig(s_log + 'log/last_plot.svg', format='svg')
    if b_plot and b_block:
        plt.show(block=True)
    return env, agent, episodes_info
