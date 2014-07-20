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


