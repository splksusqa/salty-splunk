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
                        '..', '_modules', 'lib')
if not lib_path in sys.path:
    sys.path.append(lib_path)
import requests
# salt
import salt.utils
import salt.exceptions

logger = logging.getLogger(__name__)


#### State functions ####
def installed(name,
              splunk_home,
              pkg,
              version,
              build='',
              type='splunk',
              fetcher_url='http://r.susqa.com/cgi-bin/splunk_build_fetcher.py',
              pkg_released=False,
              instances=1,
              dest='',
              install_flags='',
              start_after_install=True,
              user=''):
    """
    Install splunk if it's not installed as specified pkg

    :param str name: name of the state, sent by salt
    :param str source: pkg source, can be http, https, salt, ftp schemes
    :param str splunk_home: installdir
    :param str dest: location for storing the pkg
    :param dict install_flags: extra installation flags
    :param bool start_after_install: start splunk after installation
    :return: results of name, changes, results, and comment.
    :rtype: dict
    """
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    user = user or __salt__['pillar.get']('system:user')
    install_flags = install_flags or {}
    pkg_src = _get_pkg_url(pkg=pkg, version=version, build=build, type=type,
                           pkg_released=pkg_released,fetcher_url=fetcher_url)
    pkg_name = os.path.basename(pkg_src)
    pkg_type = _validate_pkg_for_platform(pkg_name)
    pkg_state = _get_current_pkg_state(pkg_name)
    if pkg_state['retcode'] == 1: # retcode is 1, install the pkg
        cached_pkg = __salt__['utils.cache_file'](source=pkg_src, dest=dest)
        logger.info("Installing pkg from '{s}', stored at '{c}'".format(
                    s=pkg_src, c=cached_pkg))
        if 'splunk.stop' in __salt__:
            __salt__['splunk.stop']()
        install_ret = getattr(sys.modules[__name__],
                              "_install_{t}".format(t=pkg_type))(
                          pkg=cached_pkg, splunk_home=splunk_home,
                          instances=instances, user=user, flags=install_flags)
        ret['comment'] = install_ret['comment']
        logger.info("Install runner returned code: {r}, comment: {c}".format(
                    r=install_ret['retcode'], c=install_ret['comment']))
        if install_ret['retcode'] == 0:
            if start_after_install:
                __salt__['saltutil.refresh_modules']()
                __salt__['splunk.start']()
            ret['result'] = True
            ret['changes'] = {'before': pkg_state['current_state'],
                              'after': __salt__['splunk.info']()}

    elif pkg_state['retcode'] == 2: # retcode = 2, pkg is installed already.
        ret['comment'] = pkg_state['comment']
        ret['result'] = True
    else: # retcode is 0, not going to install
        ret['comment'] = pkg_state['comment']
    return ret


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
    return cli_configured(name=name, func='listen_port', port=port, type=type,
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
    Note this is not really check a configuration or a state, but just run cli.

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


#### internal functions ####
def _get_pkg_url(pkg, version, build='', type='splunk', pkg_released=False,
        fetcher_url='http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'):
    params = {'PLAT_PKG': pkg, 'DELIVER_AS': 'url'}
    if type == 'splunkforwarder':
        params.update({'UF': '1'})
    if pkg_released:
        params.update({'VERSION': version})
    else:
        params.update({'BRANCH': version})
        if build:
            params.update({'P4CHANGE': build})
    r = requests.get(fetcher_url, params=params)
    return r.text.strip()


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
    ret = {'retcode': 127, 'comment': '', 'current_state': ''}
    reg = re.search("splunk(forwarder)?-([0-9.]+)-(\d{5,7})", pkg)
    (version, build) = (reg.group(2), reg.group(3))

    if ('splunk.is_splunk_installed' in __salt__ and
        __salt__['splunk.is_splunk_installed']()):
        current_pkg = __salt__['splunk.info']()
        ret['current_state'] = current_pkg
        ret['comment'] = "Current pkg {v}-{b} ".format(
            v=current_pkg['VERSION'], b=current_pkg['BUILD'])
        if _compare_version(current_pkg['VERSION'], version) == 'Higher':
            ret['retcode'] = 0
            ret['comment'] += "has higher version than '{p}'".format(p=pkg)
        elif _compare_version(current_pkg['VERSION'], version) == 'Same':
            if current_pkg['BUILD'] > build:
                ret['retcode'] = 0
                ret['comment'] += ("has same version, but higher build than "
                                   "'{p}'".format(p=pkg))
            elif current_pkg['BUILD'] == build:
                ret['retcode'] = 2
                ret['comment'] += ("has same version and build with "
                                   "'{p}'".format(p=pkg))
            else:
                ret['retcode'] = 1
                ret['comment'] += ("has same version, but lower build than "
                                   "'{p}'".format(p=pkg))
        else:
            ret['retcode'] = 1
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
    for n in itertools.izip_longest(v1.strip().split('.'),
                                    v2.strip().split('.'),
                                    fillvalue='0'):
        if n[0] > n[1]:
            return 'Higher'
        elif n[0] < n[1]:
            return 'Lower'
    return 'Same'


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


def _run_install_cmd(cmd, user, comment=''):
    """

    :param cmd:
    :return:
    """
    if salt.utils.is_windows():
        user = None
    ret = __salt__['cmd.run_all'](cmd, runas=user)
    if ret['retcode'] == 0:
        ret['comment'] = "Successfully ran cmd: '{c}'".format(c=cmd)
    else:
        ret['comment'] = "Cmd '{c}' returned '{r}' != 0, stderr={s}".format(
                              c=cmd, r=ret['retcode'], s=ret['stderr'])
    ret['comment'] += comment
    return ret


def _install_tgz(pkg, splunk_home, instances, flags, user):
    """
    Install tgz package, note the flags are not used.

    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    """
    cmd = "mkdir -p {s}; tar --strip-components=1 -xf {p} -C {s}".format(
           s=splunk_home, p=pkg)
    return _run_install_cmd(cmd, user)


def _install_rpm(pkg, splunk_home, instances, flags, user):
    raise NotImplementedError


def _install_msi(pkg, splunk_home, instances, flags, user):
    if not flags: flags = {}
    cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" {f} {q}'.format(
              c=pkg, h=splunk_home, q='/quiet',
              f=' '.join("{0}={1}".format(
                  t[0], str(t[1]).strip("'" '"')) for t in flags.iteritems()))
    return _run_install_cmd(cmd, user)


def _install_deb(pkg, splunk_home, instances, flags, user):
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
        comment += ("splunk_home ({s}) should be '/opt/splunk' for deb pkg! "
                    "It will have no effects".format(s=splunk_home))
    cmd = "sudo dpkg -i {p} {f}".format(p=pkg, f=flags)
    # TODO: need to handle splunk_home is not /opt/splunk, but tries to install
    # return _run_install_cmd(cmd, user) + comment
    raise NotImplementedError


def _install_Z(pkg, splunk_home, instances, flags, user):
    """

    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    """
    raise NotImplementedError


def _install_zip(pkg, splunk_home, instances, flags, user):
    """

    :param pkg:
    :param splunk_home:
    :param flags:
    :return:
    """
    raise NotImplementedError




