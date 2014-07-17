# -*- coding: utf-8 -*-
'''
Management of splunk instances
==========================
'''
__author__ = 'cchung'


import os
import logging

# salt
import salt.utils

log = logging.getLogger(__name__)


def installed(name,
              source,
              splunk_home=__salt__['splunk.get_splunkhome'],
              role='indexer'):
    '''
    work flow:
      1. get source file,
      2. determine the source file type,
      3. apply appropriate installation process (__salt__['pkg.install']??)
      4. set role
      5. restart
      6. extract the version/build, make sure it fits


    :param name:
    :param source:
    :param splunk_home:
    :return:
    '''
    pass


def removed(name):
    '''

    :param name:
    :return:
    '''
    pass

def set_role(mode, **kwargs):
    if mode.startswith('cluster'):
        if mode == 'cluster-master':
            conf = {'mode': 'master'}
        elif mode in ['cluster-searchhead', 'cluster-slave']:
            conf = {'mode': 'slave', 'master_uri': kwargs.get('master')}
        __salt__['splunk.edit_stanza']('server.conf', conf, 'clustering')



    ret = __salt__['splunk.restart']()
    return {'name': 'set_role', 'changes': {'mode': mode}, 'result': True, 'comment': ret}



