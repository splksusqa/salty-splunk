# -*- coding: utf-8 -*-
"""
Module for splunk instances
==========================
"""

__author__ = 'cchung'

import sys
import os
import platform
import subprocess
import time
import ConfigParser
import json
import logging
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'lib'))
import requests


# salt utils
import salt.utils
import salt.exceptions

__salt__ = {}
__pillar__ = {}
default_stanza = 'default'
logger = logging.getLogger('module.splunk')


class _FakeSecHead(object):
    """
    Handle conf file for key-value without section.
    This piece of codes is mainly from Alex's answer here:
    http://stackoverflow.com/questions/2819696/parsing-properties-file-in-python
    """
    def __init__(self, fp, sechead):
        self.fp = fp
        self.sechead = "[{s}]\n".format(s=sechead)

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()


def __virtual__():
    """
    Salt virtual function:
    (http://docs.saltstack.com/en/latest/ref/modules/#virtual-modules)

    :return: is_splunk_installed()
    :rtype: bool
    """
    return is_splunk_installed()


def get_splunk_home():
    """
    Get splunk_home location from pillar['splunk']['home'].

    :return: splunk_home (pillar['splunk']['home'])
    :rtype: str
    """
    home = __salt__['pillar.get']('splunk:home')
    logger.info("Getting splunk_home '{h}' from pillar".format(h=home))
    return home


def is_splunk_installed():
    """
    Check if splunk is installed at splunk_home.

    :return: True if splunk_home path exists, otherwise False.
    :rtype: bool
    """
    home = get_splunk_home()
    if os.path.exists(home):
        logger.info("Splunk is installed at '{h}'".format(h=home))
        return True
    else:
        logger.info("Splunk is Not installed at '{h}'".format(h=home))
        return False


def start():
    """
    Start splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('start')


def restart():
    """
    Restart splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('restart')


def stop():
    """
    Stop splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('stop')


def status():
    """
    Get splunk status, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('status')


def version():
    """
    Get splunk version information, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('version')


def set_splunkweb_port(port=''):
    """
    Set splunkweb port.

    :param int port:
    :return: results of calling cmd
    """
    return cmd("set web-port {p}".format(p=port))


def set_splunkd_port(port=''):
    """
    Set splunkd port.

    :param int port:
    :return: results of calling cmd
    """
    return cmd("set splunkd-port {p}".format(p=port))


def get_splunkd_port():
    """
    Get splunkd port.

    :return: splunkd port
    :rtype: str
    """
    return cmd('show splunkd-port')['stdout'].split(':')[1].strip()


def get_splunkweb_port():
    """
    Get splunkweb port.

    :return: splunkweb port
    :rtype: str
    """
    return cmd('show web-port')['stdout'].split(':')[1].strip()


def listen_port(port, type='splunktcp', options=None):
    """

    :param port:
    :param type:
    :return:
    """
    ret = {'retcode': 127, 'comment': ''}
    if options is None: options = {}
    if type == 'splunktcp':
        cmd_ = "enable listen {p}".format(p=port)
    elif type in ['udp', 'tcp']:
        cmd_ = "add {t} {p}".format(t=type, p=port)
    else:
        ret['comment'] = "Not supported listen type '{t}'".format(t=type)
        return ret
    return cmd(cmd_, options=options)


def info():
    """
    splunk product information, contains version, build, product, and platform
da
    :return: splunk.version contents
    :rtype: dict
    """
    if not is_splunk_installed():
        return {}
    f = open(os.path.join(splunk_path('etc'), 'splunk.version'), 'r')
    return dict([l.strip().split('=') for l in f.readlines()])


def cmd(command, auth='', user='', wait=True, timeout=60, options=None):
    """
    Splunk cli command.

    :param str command: command to issue
    :param str auth: authenticate string, if not specified,
    pillar['splunk']['auth'] will be used.
    :param bool wait: wait for the command to finish, default=True
    :param int timeout: timeout in seconds, default=60, only applicable when
    wait is True
    :param dict options: other cli options, key for params and value for args.
    Will automatically add dash (-) in front of each parameter.
    :return: retcode, stdout, stderr, and cmd.
    :rtype: dict
    """

    ret = {'retcode': 127, 'stdout': '', 'stderr': '', 'cmd': ''}
    options = options or {}
    if not is_splunk_installed():
        ret['stderr'] = 'Splunk is not installed'
        return ret
    auth = auth or __salt__['pillar.get']('splunk:auth')
    user = user or __salt__['pillar.get']('system:user')
    #command = 'splunk ' + command
    no_auth_cmds = ['status', 'restart', 'start', 'stop', 'version']
    for k,v in options.iteritems():
        command += " -{k} {v}".format(k=k,v=v)
    if command.split(' ')[0] in no_auth_cmds:
        if command.split(' ')[0] == 'start':
            command += ' --accept-license --no-prompt --answer-yes'
    else:
        command += " -auth {a}".format(a=auth)

    if salt.utils.is_windows():
        cwd = splunk_path('bin')
        cmd_ = "splunk " + command
    else:
        cwd = None
        cmd_ = splunk_path('bin_splunk') + " " + command

    logger.info("Running splunk cmd '{c}'".format(c=cmd_))
    ret['comment'] = __salt__['cmd.run_all'](cmd_, cwd=cwd, timeout=timeout)

    # ret = {'retcode': 127, 'stdout': '', 'stderr': '', 'cmd': ''}
    # options = options or {}
    # if not is_splunk_installed():
    #     ret['stderr'] = 'Splunk is not installed'
    #     return ret
    # auth = auth or __salt__['pillar.get']('splunk:auth')
    # cmd_ = [splunk_path('bin_splunk')] + command.split(' ')
    # no_auth_cmds = ['status', 'restart', 'start', 'stop', 'version']
    # for k,v in options.iteritems():
    #     cmd_ += ['-'+str(k), str(v)]
    # if cmd_[1] in no_auth_cmds:
    #     if cmd_[1] == 'start':
    #         cmd_ += ['--accept-license', '--no-prompt', '--answer-yes']
    # else:
    #     cmd_ += ['-auth', auth]
    #
    # ret['cmd'] = " ".join(cmd_)
    # logger.info("Running splunk cmd '{c}'".format(c=cmd_))
    # p = subprocess.Popen(cmd_, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # start_time = time.time()
    # time.sleep(0.5)
    # if wait:
    #     while True:
    #         if p.poll() == None:
    #             # raise and terminate the process while timeout
    #             if time.time() - start_time > timeout:
    #                 p.kill()
    #                 ret['stderr'] = "cmd not finished in {s}s".format(s=timeout)
    #                 logger.warn(ret['stderr'])
    #         else:
    #             break
    #         time.sleep(2)
    #     (stdout, stderr) = p.communicate()
    #     ret['stdout'] = stdout.replace('\n\n', '\n')
    #     ret['stderr'] = stderr.replace('\n\n', '\n')
    #     ret['retcode'] = p.returncode
    # else:
    #     ret['stdout'] = ''
    #     ret['stderr'] = 'Not waiting for command to complete'
    #     logger.warn(ret['stderr'])
    #     if p.returncode == 0:
    #         ret['retcode'] = 0
    # logger.debug("splunk cmd return: {r}".format(r=ret))
    return ret


def rest_call(uri, method='get', body=None, params=None, auth=None,
              base_uri='https://localhost', port=None, timeout=60,
              show_content=False, output_mode='json'):
    """
    Make a HTTP request to an endpoint

    :param str method: HTTP methods, valid: PUT, GET, POST, DELETE
    :param str uri: URI of the REST endpoint
    :param dict body: the request body
    :param dict urlparam: URL parameters
    :param str url:
    :param int port:
    :param int timeout:
    :return: retcode and comment
    :rtype: dict
    :raises CommandExecutionError:
    """
    ret = {'retcode': 127, 'comment': '', 'url': '', 'status_code': 0}
    body = body or {}
    params = params or {}
    auth = auth or __salt__['pillar.get']('splunk:auth')
    port = port or get_splunkd_port()
    valid_methods = ['get', 'post', 'put', 'delete']
    if not method.lower() in valid_methods:
        ret['comment'] = "Invalid method {m}".format(m=method)
        return ret
    if not 'output_mode' in params:
        params.update({'output_mode': output_mode})
    url = "{b}:{p}/{u}".format(b=base_uri, p=port, u=uri)
    req = getattr(requests, method)(url, params=params, data=body,
                                    timeout=timeout, verify=False,
                                    auth=tuple(auth.split(':', 1)))
    ret['status_code'] = req.status_code
    ret['url'] = req.url
    if str(req.status_code).startswith('2'):
        ret['retcode'] = 0
    if show_content:
        if output_mode == 'json':
            ret['content'] = json.loads(str(req.content))
        else:
            ret['content'] = req.content
    return ret


def add_monitor(source, index='main', wait=False, event_count=0, options=None):
    """

    :param source:
    :param index:
    :param wait:
    :param event_count:
    :return:
    """
    ret = {'retcode': 127, 'stdout': '', 'stderr': '', 'cmd': '', 'comment': ''}
    if options is None: options = {}
    if not index == 'main':
        options.update({'index': index})

    ret.update(cmd("add monitor {s}".format(s=source), options=options))
    if wait:
        ret['comment'] = _wait_until_indexing_stable(index=index,
                                                     event_count=event_count,
                                                     source=source)
        return ret
    else:
        ret['comment'] = "Not waiting for indexing to become stable."
        return ret


def _wait_until_indexing_stable(index, event_count=0, source='', sourcetype=''):
    raise NotImplementedError


def massive_cmd(command, func='cmd', flags='', parallel=False):
    """

    :param command:
    :param func:
    :param flags:
    :param parallel:
    :return:
    """
    raise NotImplementedError


def _read_config(conf_file):
    """
    read the conf from file, the key-value pairs without stanza will be applied
    as default_stanza (now is [default]).

    :param str conf_file: string of the conf file path.
    :return: ConfigParser.SafeConfigParser()
    :rtype: object
    """
    cp = ConfigParser.SafeConfigParser()
    cp.readfp(_FakeSecHead(open(conf_file, 'w+'), default_stanza))
    return cp


def _write_config(conf_file, cp):
    """

    :param str conf_file: string of the conf file path.
    :param obj cp: ConfigParser.SafeConfigParser()
    :return:
    """
    with open(conf_file, 'w+') as f:
        return cp.write(f)


def locate_conf_file(scope, conf):
    """
    locate the conf file in specified scope.

    :param scope:
    :param conf:
    :return:
    """
    return os.path.join(*[splunk_path('etc')] + scope.split(':') + [conf])


def edit_stanza(conf,
                stanza,
                scope='system:local',
                restart_splunk=False,
                action='edit'):
    """
    edit a stanza from a conf, will add the stanza if it doenst exist

    :param conf: conf file, e.g.: server.conf
    :param stanza: in dict form, e.g. {'clustering': {'mode': 'master'}}
    :param scope: splunk's conf scope, delimited by colon
    :param restart_splunk: if restart splunk after set stanza.
    :param action: perform action on conf (edit, remove)
    :returns: results
    :rtype: str
    """
    if not is_splunk_installed():
        return 'Splunk is not installed'
    if not action.strip() in ['edit', 'add', 'remove', 'delete']:
        return "Unknown action '{a}' for editing stanza".format(a=action)
    if not stanza: return "Stanza is empty!"
    conf_file = locate_conf_file(scope, conf)
    cp = _read_config(conf_file)

    # edit the whole stanza if it's a string
    if isinstance(stanza, str):
        if action.strip() in ['edit', 'add']:
            if not stanza in cp.sections():
                cp.add_section(stanza)
        else:
            if stanza in cp.sections():
                cp.remove_section(stanza)
    # edit the key value if stanza is dict.
    elif isinstance(stanza, dict):
        for s, kv in stanza.iteritems():
            if action.strip() in ['edit', 'add']:
                if not s in cp.sections():
                    cp.add_section(s)
            else:
                if not s in cp.sections():
                    return ("Stanza to remove {s} not exist, skipping".format(
                             s=s))

            if isinstance(kv, dict):
                if action.strip() in ['edit', 'add']:
                    for k, v in kv.iteritems():
                        cp.set(s, k, v)
                else:
                    for k, v in kv.iteritems():
                        cp.remove_option(s, k)
            else:
                return ("The key, value to edit is not defined as dict, type="
                        "{t}".format(t=type(kv)))
    else:
        return "Stanza is not defined as a str or dict, type={t}".format(
                   t=type(stanza))

    try:
        _write_config(conf_file, cp)
        if restart_splunk:
            restart()
        return "Successfully updated stanza {s} for conf {c}".format(
                   s=stanza, c=conf)
    except Exception as e:
        return "Failed to update conf {c}, exception: {e}".format(c=conf, e=e)


def splunk_path(path_):
    """

    :param path_:
    :return:
    """
    HOME = get_splunk_home()
    p = {
        'bin':         os.path.join(HOME, 'bin'),
        'bin_splunk':  os.path.join(HOME, 'bin', 'splunk'),
        'etc':         os.path.join(HOME, 'etc'),
        'system':      os.path.join(HOME, 'etc', 'system'),
        'apps_search': os.path.join(HOME, 'etc', 'apps', 'search'),
        'var':         os.path.join(HOME, 'var'),
        'var_log':     os.path.join(HOME, 'var', 'log'),
        'var_lib':     os.path.join(HOME, 'var', 'lib'),
        'db':          os.path.join(HOME, 'var', 'lib', 'splunk'),
        'db_main':     os.path.join(HOME, 'var', 'lib', 'splunk', 'defaultdb'),
        'db_default':  os.path.join(HOME, 'var', 'lib', 'splunk', 'defaultdb')
    }
    return p[path_]

cli = cmd
get_web_port = get_splunkweb_port
set_web_port = set_splunkweb_port

RESTURIS = {
    'APP': '/servicesNS/{u}/{a}/apps',
    'APP_TEMPLATE': '/servicesNS/{u}/{a}/apps/apptemplates',
    'APP_LOCAL': '/servicesNS/{u}/{a}/apps/local/',
    'APP_INSTALL': '/servicesNS/{u}/{a}/apps/appinstall',
    'AUTOMATIC_LOOKUP': '/servicesNS/{u}/{a}/data/props/lookups',
    'AUTHENTICATION': '/services/authentication/users',
    'CALCUALTED_FIELD': '/servicesNS/{u}/{a}/data/props/calcfields',
    'CAPABILITIES': '/services/authorization/capabilities/',
    'CHANGEPASSWORD': '/servicesNS/{u}/{a}/authentication/changepassword/',
    'CONFIG':  '/servicesNS/{u}/{a}/configs/{config}/',
    'CLUSTER_CONFIG': '/servicesNS/{u}/{a}/cluster/config',
    'CLUSTER_MASTER': '/servicesNS/{u}/{a}/cluster/master',
    'CLUSTER_SEARCHHEAD': '/servicesNS/{u}/{a}/cluster/searchhead',
    'CLUSTER_SLAVE': '/servicesNS/{u}/{a}/cluster/slave',
    'DATAMODEL_REPORT':'/services/datamodel/pivot/{dm}',
    'DATAMODEL_ACC': '/services/datamodel/model/',
    'DATAMODEL': '/servicesNS/{u}/{a}/datamodel/model/',
    'DATAMODEL_ACCELERATION': '/services/datamodel/acceleration',
    'DATAMODEL_DOWNLOAD': '/servicesNS/{u}/{a}/data/models/{dm}/download',
    'DEPLOYMENT_CLIENT_CONFIG': (
        '/servicesNS/{u}/{a}/deployment/client/config'),
    'DEPLOYMENT_SERVER_CLASSES': (
        '/servicesNS/{u}/{a}/deployment/server/serverclasses'),
    'DEPLOYMENT_SERVER_CONFIG': (
        '/servicesNS/{u}/{a}/deployment/server/config'),
    'DEPLOYMENT_SERVER_CLIENTS': (
        '/servicesNS/{u}/{a}/deployment/server/clients'),
    'DEPLOYMENT_SERVER_APPLICATION': (
        '/servicesNS/{u}/{a}/deployment/server/applications'),
    'EVENTTYPE': '/servicesNS/{u}/{a}/saved/eventtypes',
    'FIRED_ALERT': '/servicesNS/{u}/{a}/alerts/fired_alerts',
    'FIELD': '/servicesNS/{u}/{a}/search/fields',
    'FIELD_ALIAS': '/servicesNS/{u}/{a}/data/props/fieldaliases',
    'FIELD_EXTRACTION': '/servicesNS/{u}/{a}/data/props/extractions',
    'FVTAG': '/servicesNS/{u}/{a}/saved/fvtags',
    'HTTPAUTH_TOKEN': '/servicesNS/{u}/{a}/authentication/httpauth-tokens',
    'INDEX': '/servicesNS/{u}/{a}/data/indexes/',
    'INPUT_MONITOR': '/servicesNS/{u}/{a}/data/inputs/monitor',
    'INPUT_ONESHOT': '/servicesNS/{u}/{a}/data/inputs/oneshot',
    'INPUT_SCRIPT': '/servicesNS/{u}/{a}/data/inputs/script',
    'INPUT_TCP_COOKED': '/servicesNS/{u}/{a}/data/inputs/tcp/cooked',
    'INPUT_TCP_RAW': '/servicesNS/{u}/{a}/data/inputs/tcp/raw',
    'INPUT_UDP': '/servicesNS/{u}/{a}/data/inputs/udp',
    'INPUT_EVENTLOG': (
        '/servicesNS/{u}/{a}/data/inputs/win-event-log-collections'),
    'INPUT_REGMON': '/servicesNS/{u}/{a}/data/inputs/WinRegMon',
    'INPUT_PERFMON': '/servicesNS/{u}/{a}/data/inputs/win-perfmon',
    'INPUT_HOSTMON': '/servicesNS/{u}/{a}/data/inputs/WinHostMon',
    'INPUT_NETMON': '/servicesNS/{u}/{a}/data/inputs/WinNetMon',
    'INPUT_ADMON': '/servicesNS/{u}/{a}/data/inputs/ad',
    'INPUT_PRINTMON': '/servicesNS/{u}/{a}/data/inputs/WinPrintMon',
    'JOB': '/servicesNS/{u}/{a}/search/jobs',
    'LDAP': '/services/authentication/providers/LDAP/',
    'LOOKUP': '/servicesNS/{u}/{a}/data/props/lookups/',
    'LOOKUP_TRANSFORM': '/servicesNS/{u}/{a}/data/transforms/lookups/',
    'LOOKUP_TABLE_FILES': '/servicesNS/{u}/{a}/data/lookup-table-files',
    'LOGIN':'/services/auth/login',
    'MACRO': '/servicesNS/{u}/{a}/data/macros',
    'MESSAGES': '/servicesNS/{u}/{a}/messages',
    'NAVIGATION': '/servicesNS/{u}/{a}/data/ui/nav',
    'NTAG': '/servicesNS/{u}/{a}/saved/ntags',
    'PROPERTIES': '/servicesNS/{u}/{a}/properties',
    'ROLE': '/services/authorization/roles/',
    'REFRESH': '/debug/refresh',
    'SAVED_SEARCH': '/servicesNS/{u}/{a}/saved/searches',
    'SCHEDULED_VIEW': '/servicesNS/{u}/{a}/scheduled/views',
    'SEARCH_COMMANDS': '/servicesNS/{u}/{a}/search/commands',
    'SOURCETYPE': '/servicesNS/{u}/{a}/saved/sourcetypes',
    'SERVER_CONTROL_RESTART': '/services/server/control/restart/',
    'TAG': '/servicesNS/{u}/{a}/search/tags',
    'TIME': '/servicesNS/{u}/{a}/data/ui/times',
    'TRANSFORMS_EXTRACTION': (
        '/servicesNS/{u}/{a}/data/transforms/extractions'),
    'TRANSFORMS_LOOKUP': '/servicesNS/{u}/{a}/data/transforms/lookups/',
    'TRANSPARENT_SUMMARIZATION': '/servicesNS/{u}/{a}/admin/summarization',
    'TYPEAHEAD': '/servicesNS/{u}/{a}/search/typeahead/',
    'USER': '/servicesNS/{u}/{a}/authentication/users',
    'UI_MANAGER': '/servicesNS/{u}/{a}/data/ui/manager',
    'UI_PREFS': '/servicesNS/{u}/{a}/admin/ui-prefs',
    'USER_PREFS': '/servicesNS/{u}/{a}/admin/user-prefs',
    'VIEW': '/servicesNS/{u}/{a}/data/ui/views',
    'VIEWSTATES': '/servicesNS/{u}/{a}/data/ui/viewstates',
    'VIX_INDEXES': '/servicesNS/{u}/{a}/data/vix-indexes',
    'VIX_PROVIDERS': '/servicesNS/{u}/{a}/data/vix-providers',
    'WORKFLOW_ACTION': '/servicesNS/{u}/{a}/data/ui/workflow-actions'
}
