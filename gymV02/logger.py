import sys
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s;%(message)s')


def set_logger(s_mypath):
    '''
    Set a new filepath to the log file

    :param s_path: string. Folder where to place the log files

    NOTE: It really should be done in another way
    '''
    # if not s_mypath:
    #     s_mypath = s_path1
    s_mypath = s_mypath.replace('\\', '/')  # windows stuff
    if s_mypath[-1] != os.path.sep:
        s_mypath += os.path.sep
    s_log_file = s_mypath + 'log' +os.path.sep + 'agent_1.log'
    if not logger.handlers:
        # check and erase the number of log files from agents
        l_files = [x for x in os.listdir(s_mypath+'log') if 'agent' in x]
        l_files.sort()
        for s_file in l_files[4:]:
            os.remove(s_mypath + 'log' + os.path.sep + s_file)
        # rename log files
        l_files = [x for x in os.listdir(s_mypath+'log') if 'agent' in x]
        l_files.sort()
        i_total = len(l_files)
        if 'agent_1.log' in l_files:
            for i_idx, s_file in enumerate(l_files[::-1]):
                i_id = (i_total - i_idx) + 1
                # s_aux = s_file.split('_')[1]
                s_new_name = 'log' + os.path.sep + 'agent_{}.log'.format(i_id)
                s_file = 'log' + os.path.sep + s_file
                os.rename(s_mypath + s_file, s_mypath + s_new_name)
        # instanciate a logger object
        fh = logging.FileHandler(s_log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
