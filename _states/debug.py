# -*- coding: utf-8 -*-
'''
State for debugging purposes
==========================
'''
__author__ = 'cchung'

def func_test(name, arg1='', arg2=''):
    """

    :param name:
    :param arg1:
    :param arg2:
    :return:
    """
    ret = {'name': 'test',
           'changes': {'arg1': arg1, 'arg2': arg2},
           'result': False,
           'comment': ''}

    return ret
