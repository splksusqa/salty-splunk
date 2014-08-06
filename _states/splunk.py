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
              install_flags={},
              saltenv='base',
              **kwargs):
    '''
    Install splunk if it's not installed as specified pkg

    :param name: sent by salt
    :param source: pkg source, can be http, https, salt, ftp schema
    :param splunk_home: installdir
    :param install_flags: extra installation flags
    :param saltenv: saltenv, used by salt.
    :param kwargs: other kwargs.
    :return: results of changes.
    '''
    ret =  {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    pkg = os.path.basename(source)
    if _is_pkg_installed(pkg):
        ret['changes'] = {}
        ret['result'] = True
        ret['comment'] = "pkg '{p}' is already installed".format(p=pkg)
    else:
        pkg_type = _validate_pkg_for_platform(pkg)
        cached_pkg = _cache_file(source, saltenv)
        ret['comment'] = getattr(sys.modules[__name__], "_install_{t}".format(
                             t=pkg_type))(cached_pkg, splunk_home, install_flags)
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


def app_installed():



def _cache_file(source, saltenv):
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


def _run_cmd(cmd):
    '''
    :param cmd:
    :return:
    '''
    ret = __salt__['cmd.run_all'](cmd, output_loglevel='trace')
    if ret['retcode'] == 0:
        comments = "Successfully ran cmd: '{c}'".format(c=cmd)
    else:
        comments = "Cmd '{c}' returned '{r}' != 0, stderr={s}".format(
                    c=cmd, r=ret['retcode'], s=ret['stderr'])
    return comments


def _install_tgz(pkg, splunk_home, flags):
    '''
    Install tgz package, note the flags are not used.
    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    '''
    cmd = "mkdir -p {s}; tar --strip-components=1 -xf {p} -C {s}".format(
           s=splunk_home, p=pkg)
    return _run_cmd(cmd)


def _install_rpm(pkg, splunk_home, flags):
    raise NotImplementedError


def _install_msi(pkg, splunk_home, flags):
    cmd ='msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {f} {q}'.format(
             c=pkg, h=splunk_home, q='/quiet',
             f=' '.join('%s="%r"' %t for t in flags.iteritems()))
    return _run_cmd(cmd)


def _install_deb(pkg, splunk_home, flags):
    '''
    Install deb package, note that according to (http://docs.splunk.com/
    Documentation/Splunk/latest/Installation/InstallonLinux#Debian_DEB_install),
    deb package can only be installed to /opt/splunk, so splunk_home will be
    ignored.
    :param pkg: pkg location
    :param splunk_home: must be /opt/splunk for deb package
    :param flags: other installation flags
    :return:
    '''
    comments = ''
    if not splunk_home == '/opt/splunk':
        comments += ("splunk_home ({s}) should be '/opt/splunk' for deb "
                    "pkg!".format(s=splunk_home))
    cmd = "sudo dpkg -i {p} {f}".format(p=pkg, f=flags)
    # TODO: need to handle splunk_home is not /opt/splunk, but tries to install
    # return _run_cmd(cmd) + comments
    raise NotImplementedError



def _install_Z(pkg, splunk_home, flags):
    raise NotImplementedError


def _install_zip(pkg, splunk_home, flags):
    raise NotImplementedError


def set_role(method, **kwargs):
    '''
    set the role for the splunk instance
    :param mode: splunk instance mode, cluster-master, indexer, etc
    :param kwargs:
    :return:
    '''
    ret =  {'name': 'set_role', 'changes': {}, 'result': False, 'comment': ''}

    # TODO: do some validations
    if method.lower() == 'conf':
        settings = kwargs.get('stanza')
        conf = kwargs.get('conf')
        ret_set = __salt__['splunk.edit_stanza'](
                      conf=conf, stanza=settings, restart_splunk=True)
    elif method.lower() == 'rest':
        ret_set = ''
        raise NotImplementedError
    elif method.lower() == 'cli':
        ret_set = ''
        raise NotImplementedError
    else:
        raise salt.execptions.CommandExecutionError(
                   "Set role method '{m}' is not supported".format(m=method))

    ret['comment'] = ret_set
    if ret['comment'].startswith('Successfully'):
        ret['changes'] = settings
        ret['result'] = True
    return ret
    # if mode == 'cluster-master':
    #     stanza = {
    #         'clustering': {
    #             'mode': 'master'
    #         }
    #     }
    #
    # elif mode == 'cluster-slave':
    #     stanza = {
    #         'clustering': {
    #             'mode': 'slave',
    #             'master_uri': 'https://' + kwargs.get('master')
    #         },
    #         "replication_port://{p}".format(p=kwargs.get('replication_port')): {
    #         }
    #     }
    #
    # elif mode == 'cluster-searchhead':
    #     stanza = {
    #         'clustering': {
    #             'mode': 'slave',
    #             'master_uri': 'https://' + kwargs.get('master')
    #         }
    #     }
    #
    # else:
    #     raise salt.execptions.CommandExecutionError(
    #               "Role '{r}' isn't supported".format(r=mode))
    #
    # edit_stanza = __salt__['splunk.edit_stanza'](
    #                      conf='server.conf',
    #                      stanza=stanza,
    #                      restart_splunk=True)



