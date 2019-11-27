#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Implement a class to handle the command passed to the agent

@author: ucaiado

Created on 07/05/2018
'''

import json


class CommandHandler(object):
    '''
    Commands handler to the agent process parameters passed by telnet or other
    means. The API methods that users of this class might want to know are:

        on_new_command
        on_get_parameters
    '''
    def __init__(self, agent, orders):
        '''
        Initialize CommandHandler object

        :param agent: Agent object.
        :param orders: OrderHandler Object.
        '''
        self.agent = agent
        self.orders = orders

    def on_new_command(self, d_command):
        '''
        Processes the commands passed to the strategy. s_command should include
        just one command at a time and be a JSON encoded as a string in the
        format: {'param1': {'A': 1, 'B':  2}} or {'recover': 'A'}

        :param d_command: dict. command to be processed
        '''
        return False

    def on_get_parameters(self):
        '''
        Return a dictionary with all parameters used by the agent
        '''
        return {}

    def on_set_parameters(self, d_params):
        '''
        Return a list of commands to be processed by the on_command method

        :params d_params: dict. parameters passed as {'param1': {'A': 1}}
        '''
        l_rtn = []
        for s_key in d_params[self.agent._agentname]:
            s_aux = json.dumps({s_key: d_params[self.agent._agentname][s_key]})
            l_rtn.append(s_aux)
        return l_rtn

    def on_command(self, s_command):
        '''
        Processes the commands passed to the strategy. s_command should include
        just one command at a time and be a JSON encoded as a string in the
        format: {'param1': {'A': 1, 'B':  2}} or {'recover': 'A'}

        :param s_command: string. The command to be processed
        '''
        agent = self.agent
        orders = self.orders

        d_command = json.loads(s_command)
        s_log = s_command
        s_command = list(d_command.keys())[0]
        b_recover = False
        if s_command == 'recover':
            s_command = d_command['recover']
            b_recover = True
        b_processed = True
        if s_command == 'online':
            b_value = d_command[s_command]
            if b_recover:
                agent.prtbrdcast('Is it online? {}\n'.format(not agent._done))
            elif not d_command[s_command]:
                s_offline_msg = agent._mlogs['offline1']
                agent._msg_offline = s_offline_msg
                agent.set_offline()
                agent.prtbrdcast('Is it online? {}\n'.format(not agent._done))
            elif d_command[s_command]:
                agent.set_online()
                agent.prtbrdcast('Is it online? {}\n'.format(not agent._done))
        elif 'bid' in s_command:
            if b_recover:
                if agent._disable_bid:
                    agent.prtbrdcast('turn off bid side' + '\n')
                else:
                    agent.prtbrdcast('turn on bid side' + '\n')
            elif not d_command[s_command]:
                agent._disable_bid = True
                for instr in agent._instr_stack.values():
                    orders.cancel_orders_by_side(instr, 'BID', True)
                agent.prtbrdcast('turn off bid side' + '\n')
            elif d_command[s_command]:
                agent._disable_bid = False
                agent.prtbrdcast('turn on bid side' + '\n')
        elif 'ask' in s_command:
            if b_recover:
                if agent._disable_ask:
                    agent.prtbrdcast('turn off ask side' + '\n')
                else:
                    agent.prtbrdcast('turn on ask side' + '\n')
            elif not d_command[s_command]:
                agent._disable_ask = True
                for instr in agent._instr_stack.values():
                    orders.cancel_orders_by_side(instr, 'ASK', True)
                agent.prtbrdcast('turn off ask side' + '\n')
            elif d_command[s_command]:
                agent._disable_ask = False
                agent.prtbrdcast('turn on ask side' + '\n')
        elif 'init_pos' in s_command:
            if not agent.is_offline():
                s_msg = 'the agent should be offline to set new initial '
                s_msg += 'positions'
                agent.prtbrdcast(s_msg + '\n')
                return True
            # e.g. {"PETR4": {"Q": 1000, "P": 10.0}}. "P" in optional
            agent.set_initial_positions(d_command[s_command])
        else:
            b_processed = self.on_new_command(d_command)
        if not b_processed:
            s_txt = '    !!!! command "{}" is not defined\n'.format(s_log)
            agent.prtbrdcast(s_txt)
            return
        agent.prtbrdcast('    command "{}" processed\n'.format(s_log))
