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
lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if not lib_path in sys.path:
    sys.path.append(lib_path)
import requests
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# salt utils
import salt.utils
import salt.exceptions

__salt__ = {}
__pillar__ = {}
default_stanza = 'default'
logger = logging.getLogger('module.splunk')


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
        logger.info("Splunk is not installed at '{h}'".format(h=home))
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


def listen_port(port, type='splunktcp', params=None):
    """

    :param port:
    :param type:
    :return:
    """
    ret = {'retcode': 127, 'comment': ''}
    params = params or {}
    if type == 'splunktcp':
        cmd_ = "enable listen {p}".format(p=port)
    elif type in ['udp', 'tcp']:
        cmd_ = "add {t} {p}".format(t=type, p=port)
    else:
        ret['comment'] = "Not supported listen type '{t}'".format(t=type)
        return ret
    return cmd(cmd_, params=params)


def info():
    """
    splunk product information, contains version, build, product, and platform

    :return: splunk.version contents
    :rtype: dict
    """
    if not is_splunk_installed():
        return {}
    f = open(os.path.join(splunk_path('etc'), 'splunk.version'), 'r')
    return dict([l.strip().split('=') for l in f.readlines()])


def install_app(source, dest='', method='cli', **kwargs):
    """

    :param app:
    :param method:
    :param kwargs:
    :return:
    """

    if method == 'cli':
        if not os.path.exists(source):
            source = __salt__['utils.cache_file'](source=source, dest=dest)
        cmd_ = "install app {s}".format(s=source)
        return cmd(cmd_, **kwargs)
    elif method == 'rest':
        if not os.path.exists(source) and not source.startswith('http'):
            source = __salt__['utils.cache_file'](source=source, dest=dest)
        appinstall_uri = '/services/apps/appinstall'
        return rest_call(uri=appinstall_uri, method='post',
                         body={'name': source}, **kwargs)
    else:
        return "Install app method {m} is not yet supported".format(m=method)


def add_monitor(source, dest='', index='', wait=False, event_count=0,
                params=None):
    """

    :param source:
    :param index:
    :param wait:
    :param event_count:
    :return:
    """
    ret = {'retcode': 127, 'stdout': '', 'stderr': '', 'cmd': '', 'comment': ''}
    params = params or {}
    if not os.path.exists(source):
        source = __salt__['utils.cache_file'](source=source, dest=dest)
    if index: # Update params even if index=main, in case someone wants it.
        params.update({'index': index})

    ret.update(cmd("add monitor {s}".format(s=source), params=params))
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


def multi_instances(func):
    def multi(**kwargs):
        instances = __salt__['pillar.get']('splunk:instances')
        for i in instances:
            kwargs.update()
            func(**kwargs)
    raise NotImplementedError


# @multi_instances
def cmd(command, auth='', user='', splunk_home='', timeout=60, params=None):
    """
    Splunk cli command.

    :param str command: command to issue
    :param str auth: authenticate string, default: pillar['splunk']['auth']
    :param str user: user to run the command, default: pillar['system']['user']
    :param str splunk_home: splunk home to run the command, deafult:
    get_splunk_home()
    :param int timeout: timeout in seconds, default: 60
    :param dict params: other cli params, key for parameter and value for arg.
    Will automatically add dash (-) in front of each parameter.
    :return: retcode, stdout, stderr, and cmd.
    :rtype: dict
    """
    ret = {'retcode': 127, 'comment': '', 'changes': '', 'cmd': '', 'cwd': '',
           'stdout': '', 'stderr': '', 'pid': ''}
    if not is_splunk_installed():
        ret['stderr'] = 'Splunk is not installed'
        return ret
    params = params or {}
    auth = auth or __salt__['pillar.get']('splunk:auth')
    splunk_home = splunk_home or get_splunk_home()
    no_auth_cmds = ['status', 'restart', 'start', 'stop', 'version', 'help']
    for k,v in params.iteritems():
        command += " -{k} {v}".format(k=k,v=v)
    if command.split(' ')[0] in no_auth_cmds:
        if command.split(' ')[0] == 'start':
            command += ' --accept-license --no-prompt --answer-yes'
    else:
        command += " -auth {a}".format(a=auth)

    if salt.utils.is_windows():
        user = None
        cwd = splunk_path('bin', splunk_home=splunk_home)
        cmd_ = "splunk " + command
    else:
        user = user or __salt__['pillar.get']('system:user')
        cwd = ''
        cmd_ = splunk_path('bin_splunk', splunk_home=splunk_home) +" "+ command
    resp = __salt__['cmd.run_all'](cmd_, cwd=cwd, runas=user, timeout=timeout)
    resp.update({
        'stdout': os.linesep.join(
                      filter(str.strip, resp['stdout'].splitlines())),
        'stderr': os.linesep.join(
                      filter(str.strip, resp['stderr'].splitlines())),
    })
    ret.update(resp)
    ret['cmd'] = cmd_
    ret['cwd'] = cwd
    msg = ("Ran splunk cmd '{cmd}' at '{cwd}', retcode={retcode}\n"
           "stdout:\n{stdout}\nstderr:\n{stderr}".format(**ret))
    logger.info(msg)
    return ret


# @multi_instances
def rest_call(uri, method='get', body=None, params=None, auth=None,
              headers=None, base_uri='https://localhost', port=None,
              timeout=60, show_content=False, output_mode='json'):
    """
    Make a HTTP request to an endpoint

    :param str uri: uri to make request, i.e., endpoints.
    :param str method: HTTP methods, .e.g: PUT, GET, POST, DELETE
    :param dict body: the request body (i.e. -d key=value)
    :param dict params: URL parameters
    :param str auth: authentication for making request
    :param str base_uri: the base uri, contains schema://host
    :param int port: the port of the uri to request
    :param int timeout: timeout in seconds.
    :param bool show_content:
    :param str output_mode:
    :return: retcode, comment, changes, url, status_code, and content.
    :rtype: dict
    """
    ret = {'retcode': 127, 'comment': '', 'changes': '', 'url': '',
           'status_code': 0, 'content': 'Not showing content by default.'}
    body = body or {}
    params = params or {}
    auth = auth or __salt__['pillar.get']('splunk:auth')
    port = port or get_splunkd_port()
    headers = headers or {}
    valid_methods = ['get', 'post', 'put', 'delete']
    if not method.lower() in valid_methods:
        msg = "Invalid method {m}".format(m=method)
        logger.error(msg)
        ret['comment'] = msg
        return ret
    if show_content and not 'output_mode' in params:
        params.update({'output_mode': output_mode})
    url = "{b}:{p}/{u}".format(b=base_uri, p=port, u=uri)
    logger.info("Rest call to {url}, with params={params}, body={body}".format(
                **locals()))
    resp = getattr(requests, method)(url, params=params, data=body, verify=False,
                                     timeout=timeout, headers=headers,
                                     auth=tuple(auth.split(':', 1)))
    ret['status_code'] = resp.status_code
    ret['url'] = resp.url
    logger.info("Rest call to {url}, got status_code={status_code}".format(
                **ret))
    if resp.status_code == requests.codes.ok:
        ret['retcode'] = 0
    if show_content:
        if output_mode == 'json':
            ret['content'] = json.loads(str(resp.content))
        else:
            ret['content'] = resp.content
    return ret


def edit_stanza(conf, stanza, scope='system:local', restart_splunk=False,
                action='edit'):
    """
    Edit (add) or remove (delete) a key=value or whole stanza in a conf.
    If the stanza or key doenst exist, it will add one.
    For editing (removing) a whole stanza, stanza should be defined as str,
    e.g.: clustering
    For editing a key=value in a stanza, stanza should be defined as a dict as
    {stanza:{key:value}}, e.g.: {'clustering': {'replication_factor': '3'}}
    For removing a key from a stanza, stanza should be defined as {stanza: key},
    e.g.: {'main': 'maxHotBuckets'}

    :param str conf: conf file, e.g.: server.conf
    :param str/dict stanza: stanza to edit/remove, see above descriptions.
    :param str scope: conf scope, delimited by colon, e.g.: 'system:local'
    :param bool restart_splunk: restart splunk after set stanza.
    :param str action: perform an action on conf (edit, remove)
    :returns: retcode, comment, and changes
    :rtype: dict
    """
    ret = {'retcode': 127, 'comment': '', 'changes': ''}

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
                ret['changes'] = "Added section '{s}' in CP.\n".format(s=stanza)
        else:
            if stanza in cp.sections():
                cp.remove_section(stanza)
                ret['changes'] = "Removed section '{s}' in CP.\n".format(
                                 s=stanza)
            else:
                ret['comment'] += ("Section to remove '{s}' not exists, "
                                   "skipping\n".format(s=stanza))

    # edit the key value if stanza is dict.
    elif isinstance(stanza, dict):
        for s, kv in stanza.iteritems():
            # check stanza
            if action.strip() in ['edit', 'add']:
                if not s in cp.sections():
                    cp.add_section(s)
                    ret['changes'] += "Added section '{s}'\n".format(s=s)
            else:
                if not s in cp.sections():
                    ret['comment'] += ("Section '{s}' not exists for removing "
                                       "kv '{k}', skipping\n".format(s=s, k=kv))

            # edit/add key=value in the stanza
            if isinstance(kv, dict) and action.strip() in ['edit', 'add']:
                for k, v in kv.iteritems():
                    cp.set(s, k, v)
                    ret['changes'] += ("Edited kv '{k}={v}' of section '{s}' "
                                       "in CP.\n".format(k=k, v=v, s=s))
            # remove key from the stanza
            elif isinstance(kv, str) and action.strip() in ['remove', 'delete']:
                cp.remove_option(s, kv)
                ret['changes'] += ("Removed key '{k}' from section '{s}' "
                                   "in CP.\n".format(k=kv,s=s))
            else:
                msg = ("To add/edit, kv should be dict, and to remove/delete, "
                       "kv should be str, but you kv={t} for action={a}, in"
                       "stanza={s}.\n".format(t=type(kv), a=action, s=s))
                ret['comment'] += msg
                return ret
    else:
        msg = "Stanza is not str or dict, type={t}".format(t=type(stanza))
        ret['comment'] = msg
        return ret

    try:
        _write_config(conf_file, cp)
        if restart_splunk:
            restart()
        ret['retcode'] = 0
        ret['comment'] = "Successfully updated conf {c} with stanza {s}".format(
                         c=conf, s=stanza)
        return ret
    except Exception as e:
        ret['comment'] = "Failed to update conf {c}, except: {e}".format(
                         c=conf, e=e)
        return ret


class _FakeSecHead(object):
    """
    Handle conf file for key-value without section.
    This piece of codes is mainly from Alex's answer here:
    http://stackoverflow.com/questions/2819696/parsing-properties-file-in-python
    """
    def __init__(self, fp, sechead):
        self.fp = fp
        self.sechead = "[{s}]{l}".format(s=sechead, l=os.linesep)

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()


def _read_config(conf_file):
    """
    Read the conf from file, the key-value pairs without stanza will be applied
    as default_stanza (now is [default]).

    :param str conf_file: string of the conf file path.
    :return: ConfigParser.SafeConfigParser()
    :rtype: object
    """
    cp = ConfigParser.SafeConfigParser()
    cp.optionxform = str
    cp.readfp(_FakeSecHead(open(conf_file, 'r+'), default_stanza))
    return cp


def _write_config(conf_file, cp):
    """
    Write the configurations in ConfigParser into conf file.

    :param str conf_file: string of the conf file path.
    :param obj cp: ConfigParser.SafeConfigParser()
    :return: ConfigParser
    :rtype: object
    """
    with open(conf_file, 'w+') as f:
        return cp.write(f)


def locate_conf_file(scope, conf):
    """
    Locate the conf file in specified scope.

    :param scope: scope of the conf file
    :param conf: conf file
    :return: path of the conf file
    :rtype: str
    """
    return os.path.join(*[splunk_path('etc')] + scope.split(':') + [conf])


def get_file():
    raise NotImplementedError


def push_file():
    raise NotImplementedError


def get_pids(output='list'):
    """
    Get splunk pids in list or dict.

    :param str output: return form, can be 'list' or 'dict'
    :return: pid list or dict ({file: [pid list]})
    :rtype: list/dict
    """
    if output == 'list':
        pids = []
    else:
        pids = {}
    pid_dir = splunk_path('var_run_splunk')
    for f in os.listdir(pid_dir):
        if f.endswith(".pid"):
            f_path = os.path.join(pid_dir, f)
            with open(f_path, 'r') as fd:
                pid_list = [l.strip() for l in fd.readlines()]
                if output == 'list':
                    pids += pid_list
                else:
                    pids.update({f: pid_list})
    return pids


def perf(metrics=''):
    """
    Get the performance metrics of splunk.

    :param list metrics: list of metrics you want to gather.
    :return: perormance metrics.
    :rtype: dict
    """

    if not HAS_PSUTIL: return "psutil not installed."

    perf_metrics = []
    for pid in get_pids():
        p = psutil.Process(pid=int(pid))
        # TODO: drop the first time ot cpu_percent
        if salt.utils.is_windows():
            perf_metrics += [{
                'pid': p.pid,
                'name': p.name(),
                'user': p.username(),
                'cmd': " ".join(p.cmdline()),
                'io_read_bytes': p.io_counters()[2],
                'io_write_bytes': p.io_counters()[3],
                'handles': p.num_handles(),
                'threads': p.num_threads(),
                # 'threads': [dict(zip(i._fields, i)) for i in p.threads()],
                'cpu_times_user': p.cpu_times()[0],
                'cpu_times_system': p.cpu_times()[1],
                'cpu_percent': p.cpu_percent(),
                'memory_rss': p.memory_info()[0],
                'memory_vms': p.memory_info()[1],
            }]
        else:
            perf_metrics += [{
                'pid': p.pid,
                'name': p.name,
                'user': p.username,
                'cmd': " ".join(p.cmdline),
                'io_read_bytes': p.get_io_counters()[2],
                'io_write_bytes': p.get_io_counters()[3],
                'fds': p.get_num_fds(),
                'threads': p.get_num_threads(),
                # 'threads': [dict(zip(i._fields, i)) for i in p.get_threads()],
                'cpu_times_user': p.get_cpu_times()[0],
                'cpu_times_system': p.get_cpu_times()[1],
                'cpu_percent': p.get_cpu_percent(),
                'memory_rss': p.get_memory_info()[0],
                'memory_vms': p.get_memory_info()[1],
            }]
    return perf_metrics


def splunk_path(path_, splunk_home=''):
    """
    Get the path in splunk dir.

    :param path_: path
    :return: path in splunk dir.
    :rtype: str
    """
    HOME = splunk_home or get_splunk_home()
    p = {
        'bin':            os.path.join(HOME, 'bin'),
        'bin_splunk':     os.path.join(HOME, 'bin', 'splunk'),
        'etc':            os.path.join(HOME, 'etc'),
        'system':         os.path.join(HOME, 'etc', 'system'),
        'apps_search':    os.path.join(HOME, 'etc', 'apps', 'search'),
        'var':            os.path.join(HOME, 'var'),
        'var_log':        os.path.join(HOME, 'var', 'log'),
        'var_lib':        os.path.join(HOME, 'var', 'lib'),
        'var_run':        os.path.join(HOME, 'var', 'run'),
        'var_run_splunk': os.path.join(HOME, 'var', 'run', 'splunk'),
        'db':          os.path.join(HOME, 'var', 'lib', 'splunk'),
        'db_main':     os.path.join(HOME, 'var', 'lib', 'splunk', 'defaultdb'),
        'db_default':  os.path.join(HOME, 'var', 'lib', 'splunk', 'defaultdb'),
    }
    return p[path_]

cli = cmd
get_web_port = get_splunkweb_port
set_web_port = set_splunkweb_port
