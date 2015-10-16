# -*- coding: utf-8 -*-
'''
Module for debugging purposes
==========================
'''
__author__ = 'cchung'

import sys
import os
import logging
import ast
lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if not lib_path in sys.path:
    sys.path.append(lib_path)
import requests
import salt.utils
import salt.exceptions


logger = logging.getLogger(__name__)


def arg_type(arg):
    return "type of arg {t}".format(t=type(arg))


def opts(value=''):
    if not value:
        return __opts__
    return __opts__[value]


def salt_func(func, kwargs_or_args):
    kwargs = ast.literal_eval(kwargs_or_args)
    return __salt__[func](**kwargs)


def grains(value=''):
    if not value:
        return __grains__
    return __grains__[value]


def get_context(value=''):
    if not value:
        return __context__
    return __context__[value]


def get_pillar(pillar=''):
    if not pillar:
        return __pillar__
    return __pillar__[pillar]


def get_pillar_from_salt(pillar=''):
    if not pillar:
        return __salt__['pillar.data']()
    return __salt__['pillar.get'](pillar)


def log(msg='test', logger='', level='info'):
    lgr = logging.getLogger(logger)
    return getattr(lgr, level)(msg)


def check_lib(lib):
    try:
        exec "import {l}".format(l=lib)
        exec "path = {l}.__file__".format(l=lib)
        return "successfully import lib {l} from {p}".format(l=lib, p=path)
    except Exception as e:
        return "failed to import lib {l}, except: {e}".format(l=lib, e=e)


def request(url='http://httpbin.org/', method='post', data=None, headers=None):
    if data is None: data = {}
    if headers is None: headers = {'Content-type': 'application/json'}
    response = getattr(requests, method)(url+method, data=data, headers=headers)
    return response.json()