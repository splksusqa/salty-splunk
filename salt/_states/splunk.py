# -*- coding: utf-8 -*-
'''
Management of splunk instances
==========================
'''
__author__ = 'cchung'


import os
import logging
import platform
import ConfigParser

log = logging.getLogger(__name__)


def installed(name, source, install_dir=__salt__['splunk.get_home']):
    pass


def removed(name):

def set_role(mode, **kwargs):
    if mode.startswith('cluster'):
        if mode == 'cluster-master':
            conf = {'mode': 'master'}
        elif mode in ['cluster-searchhead', 'cluster-slave']:
            conf = {'mode': 'slave', 'master_uri': kwargs.get('master')}
        __salt__['splunk.edit_stanza']('server.conf', conf, 'clustering')



    ret = __salt__['splunk.restart']()
    return {'name': 'set_role', 'changes': {'mode': mode}, 'result': True, 'comment': ret}



