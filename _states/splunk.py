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

# salt
import salt.utils
import salt.exceptions

logger = logging.getLogger(__name__)


#### State functions ####
def installed(name,
              source,
              splunk_home,
              install_flags={},
              saltenv='base',
              **kwargs):
    """
    Install splunk if it's not installed as specified pkg

    :param name: sent by salt
    :param source: pkg source, can be http, https, salt, ftp schema
    :param splunk_home: installdir
    :param install_flags: extra installation flags
    :param saltenv: saltenv, used by salt.
    :param kwargs: other kwargs.
    :return: results of changes.
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    pkg = os.path.basename(source)
    pkg_state = _get_current_pkg_state(pkg)
    if pkg_state['retcode']: # install pkg
        pkg_type = _validate_pkg_for_platform(pkg)
        cached_pkg = _cache_file(source=source, saltenv=saltenv)
        __salt__['splunk.stop']()
        install_ret = getattr(sys.modules[__name__], "_install_{t}".format(
                          t=pkg_type))(cached_pkg, splunk_home, install_flags)
        ret['comment'] = install_ret['comment']
        if install_ret['retcode'] == 0:
            ret['result'] = True
            ret['changes'] = {'before': pkg_state['current_state'],
                              'after': __salt__['splunk.info']()}
        else:
            ret['result'] = False
    else: # retcode is 0, not going to install
        ret['changes'] = {}
        ret['result'] = False
        ret['comment'] = pkg_state['comment']
    return ret


def app_installed(name,
                  source,
                  dest='',
                  method='cli',
                  saltenv='base'):
    """

    :param name:
    :param source:
    :param dest:
    :param method:
    :param saltenv:
    :return:
    """
    ret = {'name': name, 'changes': {}, 'result': True, 'comment': ''}
    cached_file = _cache_file(source=source, saltenv=saltenv, dest=dest)
    ret['comment'] = __salt__['splunk.cmd']("install app {f}".format(
                         f=cached_file))

    return ret
    #raise NotImplementedError


def data_monitored(name,
                   source,
                   dest='',
                   index='main',
                   event_count=0,
                   saltenv='base'):
    """

    :param source:
    :param dest:
    :param index:
    :param wait:
    :param saltenv:
    :return:
    """
    ret = {'name': name, 'changes': {}, 'result': True, 'comment': ''}
    cached_file = _cache_file(source=source, saltenv=saltenv, dest=dest)
    ret['comment'] = __salt__['splunk.add_monitor'](source=cached_file, 
                                                    index=index, 
                                                    event_count=event_count)
    return ret


def conf_as(conf, setting):
    """

    :param conf:
    :param setting:
    :return:
    """
    ret = {'name': 'conf_as', 'changes': {}, 'result': False, 'comment': ''}
    raise NotImplementedError


def role_as(method,
            **kwargs):
    """
    set the role for the splunk instance

    :param mode: splunk instance mode, cluster-master, indexer, etc
    :param kwargs:
    :return:
    """
    ret = {'name': 'role_as', 'changes': {}, 'result': False, 'comment': ''}

    # TODO: do some validations
    if method.lower() == 'conf':
        setting = kwargs.get('setting')
        conf = kwargs.get('conf')
        ret_set = __salt__['splunk.edit_stanza'](
                      conf=conf, stanza=setting, restart_splunk=True)
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
        ret['changes'] = setting
        ret['result'] = True
    return ret


#### internal functions ####
def _is_pkg_installed(pkg):
    """
    check if splunk is installed at desired version/build

    :param pkg:
    :return:
    """
    reg = re.search("splunk(forwarder)?-([0-9.]+)-(\d{5,7})", pkg)
    (version, build) = (reg.group(2), reg.group(3))
    info = __salt__['splunk.info']()
    if info:
        if info['VERSION'] == version and info['BUILD'] == build:
            return True
    else:
        return False

def _get_current_pkg_state(pkg):
    """

    :param pkg:
    :return:
    """
    ret = {'retcode': 0, 'comment': '', 'current_state': ''}
    reg = re.search("splunk(forwarder)?-([0-9.]+)-(\d{5,7})", pkg)
    (version, build) = (reg.group(2), reg.group(3))

    if ('splunk.is_splunk_installed' in __salt__ and
        __salt__['splunk.is_splunk_installed']()):
        current_pkg = __salt__['splunk.info']()
        ret['current_state'] = current_pkg
        ret['comment'] = "Current pkg {v}-{b} ".format(
            v=current_pkg['VERSION'], b=current_pkg['BUILD'])
        if _compare_version(current_pkg['VERSION'], version) == 'Higher':
            ret['comment'] += "has high version than '{pkg}'".format(p=pkg)
        elif _compare_version(current_pkg['VERSION'], version) == 'Same':
            if current_pkg['BUILD'] > build:
                ret['comment'] += ("has same version, but higher build than "
                                   "'{p}'".format(p=pkg))
            elif current_pkg['BUILD'] == build:
                ret['comment'] += ("has same version and build with "
                                   "'{p}'".format(p=pkg), current_pkg)
            else:
                ret['retcode'] = 3
                ret['comment'] += ("has same version, but lower build than "
                                   "'{p}'".format(p=pkg))
        else:
            ret['retcode'] = 2
            ret['comment'] += "has lower version than '{p}'".format(p=pkg)
    else:
        ret['retcode'] = 1
        ret['comment'] = 'No Splunk is installed'
    return ret


def _compare_version(v1, v2):
    """

    :param v1:
    :param v2:
    :return:
    """
    if v1.strip() == v2.strip():
        return 'Same'
    for n in itertools.izip_longest(v1.strip().split('.'),
                                    v2.strip().split('.'),
                                    fillvalue='0'):
        if n[0] > n[1]:
            return 'Higher'
    return 'Lower'


def _validate_pkg_for_platform(pkg):
    """
    validate the pkg is correct for current platform, and returns the pkg type

    :param pkg: name of the package, e.g. splunk-6.1.3-217765-Linux-x86_64.tgz,
                it has to match with defined extensions (tgz, zip, msi, etc)
    :return: type of the pkg, e.g. tgz, rpm, deb.
    """
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
        raise salt.exceptions.CommandExecutionError(
                  "pkg {p} is not for platform {o}".format(p=pkg, o=os_))
    return type[0]


def _cache_file(source, saltenv, dest=''):
    """

    :param source:
    :param saltenv:
    :param dest:
    :return:
    """
    # get source file
    cache_schema = ['salt:', 'http:', 'https:', 'ftp:', 's3:']
    if any([True for i in cache_schema if source.startswith(i)]):
        cached = __salt__['cp.is_cached'](source, saltenv)
        if source.startswith('s3:'):
            if not dest:
                raise salt.exceptions.CommandExecutionError(
                          'Need a local dest to place the file from s3 bucket')

            ret = __salt__['s3.get'](source.split('/', 3)[2],
                                     source.split('/', 3)[3],
                                     local_file=dest)
            success_string = 'Saved to local file:'
            if ret.startswith(success_string):
                return ret.split(success_string)[1].strip()
            else:
                raise salt.exceptions.CommandExecutionError(ret)
        else:
            if not cached: # not cached
                cached = __salt__['cp.cache_file'](source, saltenv)
            if (__salt__['cp.hash_file'](source, saltenv) !=
                __salt__['cp.hash_file'](cached)):
                cached = __salt__['cp.cache_file'](source, saltenv)
    else: # locally stored?
        cached = source
    return cached


def _run_cmd(cmd):
    """

    :param cmd:
    :return:
    """
    ret = __salt__['cmd.run_all'](cmd, output_loglevel='trace')
    if ret['retcode'] == 0:
        ret['comment'] = "Successfully ran cmd: '{c}'".format(c=cmd)
    else:
        ret['comment'] = "Cmd '{c}' returned '{r}' != 0, stderr={s}".format(
                              c=cmd, r=ret['retcode'], s=ret['stderr'])
    return ret


def _install_tgz(pkg, splunk_home, flags):
    """
    Install tgz package, note the flags are not used.

    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    """
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
    """
    Install deb package, note that according to (http://docs.splunk.com/
    Documentation/Splunk/latest/Installation/InstallonLinux#Debian_DEB_install),
    deb package can only be installed to /opt/splunk, so splunk_home will be
    ignored.

    :param pkg: pkg location
    :param splunk_home: must be /opt/splunk for deb package
    :param flags: other installation flags
    :return:
    """
    comment = ''
    if not splunk_home == '/opt/splunk':
        comment += ("splunk_home ({s}) should be '/opt/splunk' for deb "
                    "pkg!".format(s=splunk_home))
    cmd = "sudo dpkg -i {p} {f}".format(p=pkg, f=flags)
    # TODO: need to handle splunk_home is not /opt/splunk, but tries to install
    # return _run_cmd(cmd) + comment
    raise NotImplementedError


def _install_Z(pkg, splunk_home, flags):
    """

    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    """
    raise NotImplementedError


def _install_zip(pkg, splunk_home, flags):
    """

    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    """
    raise NotImplementedError




