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

logger = logging.getLogger(__name__)


def installed(name,
              sources):
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
    ret = {'name': name, 'changes': {'sources': sources}, 'result': False, 'comment': ''}
    return ret


def removed(name):
    '''

    :param name:
    :return:
    '''
    pass

def set_role(mode, **kwargs):
    if mode == 'cluster-master':
        stanza = {
            'clustering': {'mode': 'master'}
        }

    elif mode == 'cluster-slave':
        stanza = {
            'clustering': {'mode': 'slave',
                           'master_uri': 'https://' + kwargs.get('master')},
            "replication_port://{p}".format(p=kwargs.get('replication_port')):{}
        }

    elif mode == 'cluster-searchhead':
        stanza = {
            'clustering': {'mode': 'slave',
                           'master_uri': 'https://' + kwargs.get('master')}
        }

    else:
        raise salt.execptions.CommandExecutionError(
                  "Role '{r}' isn't supported".format(r=mode))
    ret = __salt__['splunk.edit_stanza'](conf='server.conf',
                                         stanza=stanza,
                                         restart_splunk=True)

    return {'name': 'set_role', 'changes': {'mode': mode}, 'result': True, 'comment': ret}



