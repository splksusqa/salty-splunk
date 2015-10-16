# -*- coding: utf-8 -*-
"""
Management of splunk instances
==========================
"""
__author__ = 'cchung'

import os
import sys
import re
import logging
import platform
import itertools
lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        '..', 'modules', 'lib')
for path in os.listdir(lib_path):
    sys.path.append(path)
# if not lib_path in sys.path:
#     sys.path.append(lib_path)
import requests
# salt
import salt.utils
import salt.exceptions

logger = logging.getLogger(__name__)


#### State functions ####
def installed(**kwargs):
    """
    Install splunk if it's not installed as specified pkg

    :param str name: name of the state, sent by salt
    :param str source: pkg source, can be http, https, salt, ftp schemes
    :param str splunk_home: installdir
    :param str dest: location for storing the pkg, useful for future usages.
    :param dict install_flags: extra installation flags
    :param bool start_after_install: start splunk after installation
    :return: results of name, changes, results, and comment.
    :rtype: dict
    """
    return __salt__['splunk.install'](**kwargs)

def app_installed(name,
                  source,
                  **kwargs):
    """
    Install an app.

    :param name: name of the state, sent by salt
    :param source: app source, can be http,
    :param dest: location for storing the pkg, only used when source is in s3
    :param method:
    :param saltenv: saltenv, used by salt.
    :return: results of name, changes, results, and comment.
    :rtype: dict
    """
    return cli_configured(name=name, func='install_app', source=source,
                          **kwargs)


def data_monitored(name,
                   source,
                   **kwargs):
    """

    :param name: name of the state, sent by salt
    :param source:
    :param dest:
    :param saltenv:
    :param kwargs:
    :return:
    """
    return cli_configured(name=name, func='add_monitor', source=source,
                          **kwargs)


def port_listened(name,
                  port,
                  type='splunktcp',
                  **kwargs):
    """

    :param name:
    :param port:
    :param type:
    :param kwargs:
    :return:
    """
    return cli_configured(name=name, func='listen', port=port, type=type,
                          **kwargs)


def splunkd_port(name,
                 port):
    """
    Make sure splunkd port is set as specified

    :param name: name of the state, sent by salt
    :param port: port to set.
    :return: results of running splunk.cmd
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    if __salt__['splunk.get_splunkd_port']() == str(port):
        ret['result'] = True
        ret['comment'] = "splunkd is already running at port {p}".format(p=port)
        return ret
    else:
        return cli_configured(name=name, func='set_splunkd_port', port=port)


def splunkweb_port(name,
                   port):
    """
    Make sure splunkd port is set as specified

    :param name: name of the state, sent by salt
    :param port: port to set.
    :return: results of running splunk.cmd
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    if __salt__['splunk.get_splunkweb_port']() == str(port):
        ret['result'] = True
        ret['comment'] = "splunkweb is already running at port {p}".format(
                         p=port)
        return ret
    else:
        return cli_configured(name=name, func='set_splunkweb_port', port=port)


def conf_configured(name,
                    **kwargs):
    """
    Make sure conf as specified.

    :param name: name of the state, sent by salt
    :param conf:
    :param setting:
    :return:
    """
    return configured(name=name, interface='conf', **kwargs)


def rest_configured(name,
                    **kwargs):
    """

    :param name:
    :param kwargs:
    :return:
    """
    return configured(name=name, interface='rest', **kwargs)


def cli_configured(name,
                   func='cmd',
                   **kwargs):
    """
    Run cli command while state.highstate is called.
    Note this doesn't check a configuration or state, but just run cli.

    :param name:
    :param kwargs:
    :return:
    """
    return configured(name=name, interface='cli', func=func, **kwargs)


def configured(name,
               interface,
               func='cmd',
               **kwargs):
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    if interface == 'rest':
        resp = __salt__['splunk.rest_call'](**kwargs)
        ret['comment'] = (
            "Rest call returned:\n\tStatus: {status_code}\n\t"
            "Requested url: {url}\n\tContents: {content}".format(**resp))
    elif interface == 'cli':
        resp = __salt__['splunk.'+func](**kwargs)
        ret['comment'] = (
            "CLI returned:\n\tRet_code: {retcode}\n\tcmd: {cmd}\n\t"
            "stdout: {stdout}\n\tstderr: {stderr}".format(**resp))
    elif interface == 'conf':
        resp = __salt__['splunk.edit_stanza'](**kwargs)
        ret['comment'] = (
            "Editing conf returned:\n\tRet_code: {retcode}\n\t"
            "Changes: {changes}\n\tcomment: {comment}".format(**resp))
    else:
        valid = ['rest', 'cli', 'conf']
        raise salt.execptions.CommandExecutionError(
            "Invalid config interface '{i}', valid are {v}".format(i=interface,
                                                                   v=valid))
    if resp['retcode'] == 0:
        ret['result'] = True
    return ret




