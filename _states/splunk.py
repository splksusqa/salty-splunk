# -*- coding: utf-8 -*-
'''
Management of splunk instances
==========================
'''
__author__ = 'cchung'

import os
import sys
import re
import logging
import platform

# salt
import salt.utils
import salt.exceptions

logger = logging.getLogger(__name__)

def installed(name,
              source,
              splunk_home,
              installer_flags={},
              saltenv='base',
              **kwargs):
    '''
    Install splunk if it's not installed as specified pkg

    :param name: sent by salt
    :param source: pkg source, can be http, https, salt, ftp schema
    :param splunk_home: installdir
    :param installer_flags: extra installation flags
    :param saltenv: saltenv, used by salt.
    :param kwargs: other kwargs.
    :return: results of changes.
    '''
    ret =  {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    if not splunk_home:
        splunk_home = __salt__['splunk.get_splunk_home']()

    pkg = os.path.basename(source)
    if _is_pkg_installed(pkg):
        ret['changes'] = {}
        ret['comment'] = "pkg '{p}' is already installed".format(p=pkg)
        return ret

    pkg_type = _validate_pkg_for_platform(pkg)
    cached_pkg = _cache_pkg(source, saltenv)

    getattr(sys.modules[__name__], "_install_{t}".format(t=pkg_type))(
        cached_pkg, splunk_home, installer_flags)
    ret['changes'] = __salt__['splunk.info']()
    ret['result'] = True
    return ret


def _is_pkg_installed(pkg):
    '''
    check if splunk is installed at desired version/build
    :param pkg:
    :return:
    '''
    reg = re.search("splunk(forwarder)?-([0-9.]+)-(\d{5,7})", pkg)
    (version, build) = (reg.group(2), reg.group(3))
    info = __salt__['splunk.info']()
    if info:
        if info['VERSION'] == version and info['BUILD'] == build:
            return True
    else:
        return False


def _validate_pkg_for_platform(pkg):
    '''
    validate the pkg is correct for current platform, and returns the pkg type
    :param pkg: name of the package, e.g. splunk-6.1.3-217765-Linux-x86_64.tgz,
                it has to match with defined extensions (tgz, zip, msi, etc)
    :return: type of the pkg, e.g. tgz, rpm, deb.
    '''
    matrix = {
        'msi': 'Windows',
        'zip': 'Windows',
        'tgz': 'Linux', # TODO: need to handle tgz for Darwin
        'rpm': 'Linux',
        'deb': 'Linux',
        'Z': 'SunOS',
    }
    os_ = platform.system()
    type = [t for t in matrix if pkg.endswith(t) and os_ == matrix[t]]
    if not type:
        raise salt.exceptions.SaltInvocationError(
                  "pkg {p} is not for platform {o}".format(p=pkg, o=os_))
    return type[0]


def _cache_pkg(source, saltenv):
    # get source file
    pkg_to_cache = ['salt:', 'http:', 'https:', 'ftp:']
    if any([True for i in pkg_to_cache if source.startswith(i)]):
        cached_pkg = __salt__['cp.is_cached'](source, saltenv)
        if not cached_pkg: # not cached
            cached_pkg = __salt__['cp.cache_file'](source, saltenv)
        if (__salt__['cp.hash_file'](source, saltenv) !=
            __salt__['cp.hash_file'](cached_pkg)):
            cached_pkg = __salt__['cp.cache_file'](source, saltenv)
    else: # locally stored?
        cached_pkg = source
    return cached_pkg


def _install_tgz():
    raise NotImplementedError


def _install_rpm():
    raise NotImplementedError


def _install_msi(pkg, splunk_home, flags):
    cmd ='msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {f}'.format(
             c=pkg, h=splunk_home,
             f=' '.join('%s="%r"' %t for t in flags.iteritems()))
    return __salt__['cmd.run'](cmd+' /quiet', output_loglevel='trace')


def _install_deb():
    raise NotImplementedError


def _install_Z():
    raise NotImplementedError


def _install_zip():
    raise NotImplementedError


def removed(name):
    '''

    :param name:
    :return:
    '''
    ret =  {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    raise NotImplementedError


def set_role(mode, **kwargs):
    '''
    set the role for the splunk instance
    :param mode: splunk instance mode, cluster-master, indexer, etc
    :param kwargs:
    :return:
    '''
    ret =  {'name': 'set_role', 'changes': {}, 'result': False, 'comment': ''}

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
    ret['comment'] = __salt__['splunk.edit_stanza'](
                         conf='server.conf',
                         stanza=stanza,
                         restart_splunk=True)
    if ret['comment'].startswith('Successfully'):
        ret['result'] = True
    return ret


