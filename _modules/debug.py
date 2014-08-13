# -*- coding: utf-8 -*-
'''
Module for debugging purposes
==========================
'''
__author__ = 'cchung'


import salt.utils
import salt.exceptions


def arg_type(arg):
    """

    :param arg:
    :return:
    """
    return "type of arg {t}".format(t=type(arg))


def get_opts(value=''):
    """

    :param value:
    :return:
    """
    if not value:
        return __opts__
    else:
        return __opts__[value]

def get_salt(func, **kwargs):
    """

    :param func:
    :param kwargs:
    :return:
    """
    return __salt__[func](**kwargs)

def get_grains(value=''):
    """

    :param value:
    :return:
    """
    if not value:
        return __grains__
    else:
        return __grains__[value]

def get_context(value=''):
    """

    :param value:
    :return:
    """
    if not value:
        return __context__
    else:
        return __context__[value]

def check_lib(lib):
    """

    :param lib:
    :return:
    """
    try:
        exec "import {l}".format(l=lib)
        return "successfully import lib {l}".format(l=lib)
    except Exception as e:
        return "failed to import lib {l}, except: {e}".format(l=lib, e=e)
