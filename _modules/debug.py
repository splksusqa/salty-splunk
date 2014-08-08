# -*- coding: utf-8 -*-
'''
Module for debugging purposes
==========================
'''
__author__ = 'cchung'


import salt.utils
import salt.exceptions


def arg_type(arg):
    return "type of arg {t}".format(t=type(arg))


def get_opts(value=''):
    if not value:
        return __opts__
    else:
        return __opts__[value]

def get_salt(func, **kwargs):
    return __salt__[func](**kwargs)

def get_grains(value=''):
    if not value:
        return __grains__
    else:
        return __grains__[value]

def get_context(value=''):
    if not value:
        return __context__
    else:
        return __context__[value]


