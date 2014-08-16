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

logger = logging.getLogger('state.splunk')


#### State functions ####
def installed(name,
              source,
              splunk_home,
              dest='',
              install_flags='',
              saltenv='base'):
    """
    Install splunk if it's not installed as specified pkg

    :param name: name of the state, sent by salt
    :param source: pkg source, can be http, https, salt, ftp schema
    :param splunk_home: installdir
    :param dest: location for storing the pkg, only used when source is in s3
    :param install_flags: extra installation flags
    :param saltenv: saltenv, used by salt.
    :return: results of name, changes, results, and comment.
    :rtype: dict
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    pkg = os.path.basename(source)
    pkg_type = _validate_pkg_for_platform(pkg)
    pkg_state = _get_current_pkg_state(pkg)
    if pkg_state['retcode']: # retcode is not 0, install the pkg
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
    Install an app.

    :param name: name of the state, sent by salt
    :param source: app source, can be http,
    :param dest: location for storing the pkg, only used when source is in s3
    :param method:
    :param saltenv: saltenv, used by salt.
    :return: results of name, changes, results, and comment.
    :rtype: dict
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
                   saltenv='base',
                   **kwargs):
    """

    :param name: name of the state, sent by salt
    :param source:
    :param dest:
    :param index:
    :param wait:
    :param saltenv:
    :return:
    """
    ret = {'name': name, 'changes': {}, 'result': True, 'comment': ''}
    cached_file = _cache_file(source=source, saltenv=saltenv, dest=dest)
    ret['comment'] = __salt__['splunk.add_monitor'](
                         source=cached_file, index=index, wait=wait,
                         event_count=event_count, options=kwargs)
    return ret


def port_listened(name,
                  port,
                  type='splunktcp',
                  **kwargs):
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    result = __salt__['splunk.listen_port'](port=port, type=type,
                                            options=kwargs)
    raise NotImplementedError


def splunkd_port(name,
                 port):
    """
    Make sure splunkd port is set as specified

    :param name: name of the state, sent by salt
    :param port: port to set.
    :return: results of running splunk.cmd
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    result = __salt__['splunk.set_splunkd_port'](port=port)
    ret['comment'] = result
    if result['retcode'] == 0:
        ret['result'] = True
    return ret


def splunkweb_port(name,
                   port):
    """
    Make sure splunkd port is set as specified

    :param name: name of the state, sent by salt
    :param port: port to set.
    :return: results of running splunk.cmd
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    result = __salt__['splunk.set_splunkweb_port'](port=port)
    ret['comment'] = result
    if result['retcode'] == 0:
        ret['result'] = True
    return ret


def conf_configured(name,
                    conf,
                    stanza,
                    restart_splunk=True):
    """
    Make sure conf as specified.

    :param name: name of the state, sent by salt
    :param conf:
    :param setting:
    :return:
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    __salt__['splunk.edit_stanza'](
        conf=conf, stanza=stanza, restart_splunk=restart_splunk)
    raise NotImplementedError


def rest_configured(name,
                    **kwargs):
    """

    :param name:
    :param kwargs:
    :return:
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    result = __salt__['splunk.rest_call'](**kwargs)
    #ret['comment'] = result
#     if result['retcode'] == 0:
#         ret['result'] = T
    ret['comment'] = result

    return ret


def role_configured(name,
                    method,
                    **kwargs):
    """
    set the role for the splunk instance

    :param name: name of the state, sent by salt
    :param mode: splunk instance mode, cluster-master, indexer, etc
    :param kwargs:
    :return:
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    setting = kwargs.get('setting')

    # TODO: do some validations
    if method.lower() == 'conf':
        conf = kwargs.get('conf')
        ret.update(conf_configured(name=name, conf=conf, stanza=setting))
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
            ret['comment'] += "has high version than '{p}'".format(p=pkg)
        elif _compare_version(current_pkg['VERSION'], version) == 'Same':
            if current_pkg['BUILD'] > build:
                ret['comment'] += ("has same version, but higher build than "
                                   "'{p}'".format(p=pkg))
            elif current_pkg['BUILD'] == build:
                ret['comment'] += ("has same version and build with "
                                   "'{p}'".format(p=pkg))
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
    if not flags: flags = {}
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




