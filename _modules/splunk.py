# -*- coding: utf-8 -*-
"""
Module for splunk instances
==========================
"""

__author__ = 'cchung'

import sys
import os
import re
import ConfigParser
import json
import logging
import inspect
import shutil
import socket
import platform
from functools import wraps
from distutils.version import LooseVersion
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
logger = logging.getLogger(__name__)


rest_endpoints = {
    #'indexes': 'servicesNS/nobody/_cluster/data/indexes/',
    'indexes': "services/data/indexes/{idx}",
    'appinstall': 'services/apps/appinstall',
    'splunktcp': 'servicesNS/nobody/search/data/inputs/tcp/cooked',
    'tcp': 'servicesNS/nobody/search/data/inputs/tcp/raw',
    'udp': 'servicesNS/nobody/search/data/inputs/udp',
}


#### Decorators ####

def log(func):
    @wraps(func)
    def l(*args, **kwargs):
        ret = func(*args, **kwargs)
        logger.info("Function '{f}' with '{v}' returned '{r}'".format(
                        f=func.__name__, v=kwargs, r=ret))
        return ret
    return l


def multi_instances(func):
    @wraps(func)
    def multi(*args, **kwargs):
        instances = __pillar__['splunk']['instances']
        splunk_home_base = kwargs.get('home')
        splunk_port_base = kwargs.get('port')
        ret = {}
        for i in xrange(instances):
            kwargs.update({
                'splunk_home': splunk_home_base + '_' + str(i),
                'port': int(splunk_port_base) + i
            })
            ret.update({ splunk_home_base + '_' + str(i): func(**kwargs)})
        return ret
    return multi


def splunk_installed(func):
    @wraps(func)
    def checked(*args, **kwargs):
        if not is_splunk_installed():
            raise
        return func(**kwargs)
    return checked


#### Salt functions ####

def __virtual__():
    """
    Salt virtual function:
    (http://docs.saltstack.com/en/latest/ref/modules/#virtual-modules)

    :return: is_splunk_installed()
    :rtype: bool
    """
    return True


def home():
    """
    Get splunk_home location from pillar['splunk']['home'].

    :return: splunk_home (pillar['splunk']['home'])
    :rtype: str
    """
    return __pillar__['splunk']['home']


def is_splunk_installed():
    """
    Check if splunk is installed at splunk_home.

    :return: True if splunk_home path exists, otherwise False.
    :rtype: bool
    """
    splunk_home = home()
    is_installed = os.path.exists(_path('bin'))
    logger.info("Splunk {i}installed at '{h}'".format(
                   i='' if is_installed else 'not ', h=splunk_home))
    return is_installed


def start():
    """
    Start splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('start')['stdout']


def restart():
    """
    Restart splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('restart')['stdout']


def stop(force=False):
    """
    Stop splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('stop' + (' -f' if force else ''))['stdout']


def status():
    """
    Get splunk status, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('status')['stdout']


def version():
    """
    Get splunk version information, wrapped to cmd.

    :return: results of calling cmd
    """
    return cmd('version')['stdout']


def set_splunkweb_port(port=''):
    """
    Set splunkweb port.

    :param int port:
    :return: results of calling cmd
    """
    stanza = {'settings': {'httpport': str(port)}}
    return edit_stanza(conf='web.conf', stanza=stanza)


def set_splunkd_port(port=''):
    """
    Set splunkd port, set remote splunkd is not supported.

    :param int port:
    :return: results of calling cmd
    """
    stanza = {'settings': {'mgmtHostPort': "127.0.0.1:{p}".format(p=str(port))}}
    return edit_stanza(conf='web.conf', stanza=stanza)


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


@log
def get_mgmt_uri(scheme=True, **kwargs):
    """
    Get splunk mgmt uri
    :return: splunk mgmt uri
    :rtype: str
    """
    mgmt_uri = socket.gethostname().strip() + ':' + get_splunkd_port()
    if scheme:  ## TODO: might not be https...
        mgmt_uri = 'https://' + mgmt_uri
    return mgmt_uri


@log
def get_listening_uri(type='splunktcp', ordinal=0, **kwargs):
    """

    :return:
    """
    contents = rest_call(uri=rest_endpoints[type], show_content=True)
    ports = [i['name'] for i in contents['content']['entry']]
    if len(ports) == 0:
        raise salt.exceptions.CommandExecutionError("No splunktcp port avail.")
    return socket.gethostname().strip() + ':' + ports[ordinal]


@log
def listen(port, type='splunktcp', params=None, **kwargs):
    """

    :param port:
    :param type:
    :return:
    """
    ret = {'retcode': 127, 'comment': ''}
    if not is_splunk_installed():
        ret['comment'] = 'Splunk is not installed'
        return ret
    params = params or {}
    if type == 'splunktcp':
        cmd_ = "enable listen {p}".format(p=port)
    elif type in ['udp', 'tcp']:
        cmd_ = "add {t} {p}".format(t=type, p=port)
    else:
        ret['comment'] = "Not supported listen type '{t}'".format(t=type)
        return ret
    return cmd(cmd_, params=params)


@log
def info(**kwargs):
    """
    splunk product information, contains version, build, product, and platform

    :return: splunk.version contents
    :rtype: dict
    """
    if not is_splunk_installed():
        return {}
    f = open(os.path.join(_path('etc'), 'splunk.version'), 'r')
    return dict([l.strip().split('=') for l in f.readlines()])


@log
def install_app(source, dest='', method='cli', **kwargs):
    """

    :param app:
    :param method:
    :param kwargs:
    :return:
    """
    if method == 'cli':
        source = __salt__['utils.cache_file'](source=source, dest=dest)
        cmd_ = "install app {s}".format(s=source)
        return cmd(cmd_, **kwargs)
    elif method == 'rest':
        if not source.startswith('http'):
            source = __salt__['utils.cache_file'](source=source, dest=dest)
        return rest_call(uri=rest_endpoints['appinstall'], method='post',
                         body={'name': source}, **kwargs)
    else:
        return "Install app method {m} is not supported".format(m=method)


@log
def add_monitor(source, dest='', index='', wait=False, event_count=0,
                params=None, **kwargs):
    """

    :param source:
    :param index:
    :param wait:
    :param event_count:
    :return:
    """
    ret = {'retcode': 127, 'stdout': '', 'stderr': '', 'cmd': '', 'comment': ''}
    if not is_splunk_installed():
        ret['comment'] = 'Splunk is not installed'
        return ret
    params = params or {}
    source = __salt__['utils.cache_file'](source=source, dest=dest)
    if index:
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


@log
def _wait_until_indexing_stable(index, event_count=0, source='', sourcetype='',
                                **kwargs):
    raise NotImplementedError


@log
def massive_cmd(command, func='cmd', flags='', parallel=False):
    """

    :param command:
    :param func:
    :param flags:
    :param parallel:
    :return:
    """
    raise NotImplementedError



@log
def cmd(command, auth='', user='', timeout=120, params=None, **kwargs):
    """
    Splunk cli command.

    :param str command: command to issue
    :param str auth: authenticate string, default: pillar['splunk']['auth']
    :param str user: user to run the command, default: pillar['system']['user']
    :param int timeout: timeout in seconds, default: 60
    :param dict params: other cli params, key for parameter and value for arg.
    Will automatically add dash (-) in front of each parameter.
    :return: retcode, stdout, stderr, and cmd.
    :rtype: dict
    """
    ret = {'retcode': 127, 'cmd': '', 'cwd': '',
           'stdout': '', 'stderr': '', 'pid': ''}
    if not is_splunk_installed():
        ret['comment'] = 'Splunk is not installed'
        return ret
    params = params or {}
    auth = auth or __pillar__['splunk']['auth']
    no_auth_cmds = ['status', 'restart', 'start', 'stop', 'version', 'help',
                    'btool']
    for k,v in params.iteritems():
        command += " -{k} {v}".format(k=k,v=v)
    if os.path.exists(_path('ftr')) or os.path.exists(_path('.ftr')):
        command += ' --accept-license --no-prompt --answer-yes'
    if not command.split(' ')[0] in no_auth_cmds:
        command += " -auth {a}".format(a=auth)

    if salt.utils.is_windows():
        user = None
        cwd = _path('bin')
        cmd_ = "splunk " + command
    else:
        user = user or __pillar__['system']['user']
        cwd = ''
        cmd_ = _path('bin:splunk') +" "+ command
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
    return ret


@log
def rest_call(uri, method='get', body=None, params=None, auth=None,
              headers=None, base_uri='https://localhost', port=None,
              timeout=60, show_content=False, output_mode='json', **kwargs):
    """
    Make a HTTP request to an endpoint

    :param str uri: uri to make request, i.e., endpoints.
    :param str method: HTTP methods, .e.g: PUT, GET, POST, DELETE
    :param dict body: the request body (i.e. -d key=value)
    :param dict params: URL parameters
    :param str auth: authentication for making request
    :param str base_uri: the base uri, contains scheme://host
    :param int port: the port of the uri to request
    :param int timeout: timeout in seconds.
    :param bool show_content: if showing the response contents of the request.
    :param str output_mode: output to json or
    :return: retcode, comment, changes, url, status_code, and content.
    :rtype: dict
    """
    ret = {'retcode': 127, 'comment': '', 'changes': '', 'status_code': 0,
           'url': '', 'content': 'Not showing response contents by default.'}
    if not is_splunk_installed():
        ret['comment'] = 'Splunk is not installed'
        return ret
    body = body or {}
    auth = auth or __pillar__['splunk']['auth']
    port = port or get_splunkd_port()
    params = params or {}
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
    resp = getattr(requests, method.lower())(url, params=params, data=body,
                                             verify=False, timeout=timeout,
                                             headers=headers,
                                             auth=tuple(auth.split(':', 1)))
    ret['status_code'] = resp.status_code
    ret['url'] = resp.url
    logger.info("Rest call to {url}, got status_code={status_code}".format(
                **ret))
    if resp.status_code in [200, 201, 202, 203, 204]:
        ret['retcode'] = 0
    if show_content:
        if output_mode == 'json':
            ret['content'] = json.loads(str(resp.content))
        else:
            ret['content'] = resp.content
    return ret


@log
def edit_stanza(conf, stanza, scope='system:local', restart_splunk=False,
                action='edit', **kwargs):
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
        ret['comment'] = 'Splunk is not installed'
        return ret
    if not action.strip() in ['edit', 'add', 'remove', 'delete']:
        return "Unknown action '{a}' for editing stanza".format(a=action)
    if not stanza: return "Stanza is empty!"
    conf_file = locate_conf_file(scope, conf)
    conf_dir = os.path.dirname(conf_file)
    if not os.path.exists(conf_dir):
        __salt__['utils.mkdirs'](conf_dir)
        ret['comment'] += "Created dir {c}, ".format(c=conf_dir)
    cp = _read_config(conf_file)

    # edit the whole stanza if it's a string
    if isinstance(stanza, str):
        if action.strip() in ['edit', 'add']:
            if not stanza in cp.sections():
                cp.add_section(stanza)
                ret['changes'] = "\nAdded section '{s}'.".format(s=stanza)
        else:
            if stanza in cp.sections():
                cp.remove_section(stanza)
                ret['changes'] = "\nRemoved section '{s}'.".format(
                                 s=stanza)
            else:
                ret['comment'] += ("\nSection to remove '{s}' not exists, "
                                   "skipping".format(s=stanza))

    # edit the key value if stanza is dict.
    elif isinstance(stanza, dict):
        for s, kv in stanza.iteritems():
            # check stanza
            if action.strip() in ['edit', 'add']:
                if not s in cp.sections():
                    cp.add_section(s)
                    ret['changes'] += "\nAdded section '{s}'.".format(s=s)
            else:
                if not s in cp.sections():
                    ret['comment'] += ("\nSection '{s}' not exists for removing"
                                       " kv '{k}', skipping".format(s=s, k=kv))

            # edit/add key=value in the stanza
            if isinstance(kv, dict) and action.strip() in ['edit', 'add']:
                for k, v in kv.iteritems():
                    cp.set(s, k, v)
                    ret['changes'] += ("\nEdited kv '{k}={v}' of section '{s}'"
                                       ".".format(k=k, v=v, s=s))
            # remove key from the stanza
            elif isinstance(kv, str) and action.strip() in ['remove', 'delete']:
                cp.remove_option(s, kv)
                ret['changes'] += ("\nRemoved key '{k}' from section '{s}'"
                                   ".".format(k=kv,s=s))
            else:
                msg = ("\nTo add/edit, kv should be dict, and to remove/delete,"
                       " kv should be str, but you kv={t} for action={a}, in"
                       "stanza={s}.".format(t=type(kv), a=action, s=s))
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


#### Internal functions ####

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


@log
def _read_config(conf_file, **kwargs):
    """
    Read the conf from file, the key-value pairs without stanza will be applied
    as default_stanza (now is [default]).

    :param str conf_file: string of the conf file path.
    :return: ConfigParser.SafeConfigParser()
    :rtype: object
    """
    # handle unicode endings, SQA-420
    content = open(conf_file, 'r+').read()
    for e in [r'\xfe\xff', r'\xff\xfe', r'\xef\xbb\xbf']:
        content = re.sub(e, '', content)
    open(conf_file, 'w+').write(content)
    # read as ConfigParser (cp)
    cp = ConfigParser.SafeConfigParser()
    cp.optionxform = str
    cp.readfp(_FakeSecHead(open(conf_file, 'a+'), default_stanza))
    return cp


@log
def _write_config(conf_file, cp, **kwargs):
    """
    Write the configurations in ConfigParser into conf file.

    :param str conf_file: string of the conf file path.
    :param obj cp: ConfigParser.SafeConfigParser()
    :return: ConfigParser
    :rtype: object
    """
    with open(conf_file, 'w+') as f:
        return cp.write(f)


@log
def locate_conf_file(scope, conf, **kwargs):
    """
    Locate the conf file in specified scope.

    :param scope: scope of the conf file
    :param conf: conf file
    :return: path of the conf file
    :rtype: str
    """
    return os.path.join(*[_path('etc')] + scope.split(':') + [conf])


@log
def get_file(source, dest='', **kwargs):
    """
    Get a file from source and save it to dest inside splunk dir.
    Available source schemes are s3://, http://, https://, salt://
    dest format is dir:sub_dir_1:sub_dir_2:filename,
    you can also use dir:sub_dir_1:sub_dir_2 if sub_dir_2 already exists.

    :param str source: file uri.
    :param str dest: file path inside splunk home.
    :return: file path on minion (or error messages.)
    :rtype: str
    """
    return __salt__['utils.cache_file'](source=source, dest=_path(dest))


@log
def push_file(source, **kwargs):
    """
    Push a file inside splunk up to salt-master, and save it to cachedir of
    salt-master, source format is dir:sub_dir_1:sub_dir_2:filename,
    cachedir default is /var/cache/salt/master/minions/minion-id/files/

    :param source: file path inside splunk home.
    :return: if the file is successfully pushed to salt-master
    :rtype: bool
    """
    return __salt__['cp.push'](_path(source))


@log
def check_log(type='crash', **kwargs):
    raise NotImplementedError


@log
def check_crash(**kwargs):
    raise NotImplementedError


@log
def check_errors(logfile='', allowed=5, **kwargs):
    raise NotImplementedError


@log
def event_count(host=None, source=None, sourcetype=None, **kwargs):
    raise NotImplementedError


@log
def total_event_count(index='main', method='rest', **kwargs):
    if method == 'rest':
        uri = rest_endpoints['indexes'].format(idx=index)
        count = rest_call(uri, show_content=True
                    )['content']['entry'][0]['content']['totalEventCount']
    elif method == 'file':
        raise NotImplementedError
    else:
        raise NotImplementedError

    return count


@log
def get_pids(output='list', **kwargs):
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
    pid_dir = _path('var:run:splunk')

    if os.path.exists(pid_dir):
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


@log
def perf(verbose=False, **kwargs):
    """
    Get the performance metrics of splunk.

    :param bool verbose: gather more detailed data.
    :return: performance metrics.
    :rtype: dict
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))

    if not HAS_PSUTIL:
        return "psutil not installed."

    perf_metrics = []
    for pid in get_pids():
        try:
            metrics = _get_perf_metrics(pid, verbose)
            perf_metrics += [metrics]
        except psutil.NoSuchProcess:
            pass

    return perf_metrics


@log
def _get_perf_metrics(pid, verbose, **kwargs):
    p = psutil.Process(pid=int(pid))
    p.get_cpu_percent()  # drop the first time ot cpu_percent

    if not salt.utils.is_windows():
        metrics_map = {
            'num_handles':      'get_num_fds',
            #'children':         'get_children',
            'connections':      'get_connections',
            'cpu_affinity':     'get_cpu_affinity',
            'cpu_percent':      'get_cpu_percent',
            'cpu_times':        'get_cpu_times',
            'memory_info_ex':   'get_ext_memory_info',
            'io_counters':      'get_io_counters',
            'memory_info':      'get_memory_info',
            'memory_maps':      'get_memory_maps',
            #'memory_percent':   'get_memory_percent',
            'num_ctx_switches': 'get_num_ctx_switches',
            'num_threads':      'get_num_threads',
            'open_files':       'get_open_files',
            #'rlimit':           'get_rlimit',
            'threads':          'get_threads',
            #'cwd':              'getcwd',
        }
        for m in metrics_map:  # set attr for compatibility.
            setattr(p, m, getattr(p, metrics_map[m]))
    else:  # set func as attr on windows
        p.name = p.name()
        p.username = p.username()
        p.cmdline = p.cmdline()

    # gather the metrics
    metrics = {
        'pid': p.pid,
        'name': p.name,
        'user': p.username,
        'cmd': " ".join(p.cmdline),
        'io_read_bytes': p.io_counters()[2],
        'io_write_bytes': p.io_counters()[3],
        'fds': p.num_handles(),
        'threads': p.num_threads(),
        'cpu_times_user': p.cpu_times()[0],
        'cpu_times_system': p.cpu_times()[1],
        'cpu_percent': p.cpu_percent(),
        'memory_rss': p.memory_info()[0],
        'memory_vms': p.memory_info()[1],
    }
    if verbose:  # the followings are the metrics we can get without issues.
        metrics.update({
            'ctx_switches_voluntary':   p.num_ctx_switches()[0],
            'ctx_switches_involuntary': p.num_ctx_switches()[1],
            'memory_shared': p.memory_info_ex()[2],
            'memory_text':   p.memory_info_ex()[3],
            'memory_lib':    p.memory_info_ex()[4],
            'memory_data':   p.memory_info_ex()[5],
            'memory_dirty':  p.memory_info_ex()[6],
            'memory_maps': _named_tuple_list_to_dict_list(p.memory_maps()),
            'thread_info': _named_tuple_list_to_dict_list(p.get_threads()),
            'open_files':  _named_tuple_list_to_dict_list(p.open_files()),
            'connections': _named_tuple_list_to_dict_list(p.connections())
        })
    return metrics


@log
def uninstall(**kwargs):
    """
    Uninstall splunk, this
    :return:
    """

    ret = {'comment': '', 'retcode': 127}
    for pid in get_pids():
        try:
            os.kill(int(pid), 9)
        except OSError:
            pass
    splunktype = __pillar__['splunk']['type']
    if splunktype == 'splunk':
        product = "splunk"
        if (LooseVersion(__pillar__['splunk']['version']) >=
                LooseVersion('6.2.0') or
            __pillar__['splunk']['version'] in ['dash', 'ember', 'current']):
            product = "SplunkEnterprise"
        services = ['splunkd', 'splunkweb']
    elif splunktype == 'splunkforwarder':
        product = "UniversalForwarder"
        services = ['splunkforwarder']
    else:
        product = ""
        services = []

    if salt.utils.is_windows() and product and services:
        sc_cmd = " & ".join(["sc {0} {1}".format(action, service)
                              for action in ['stop', 'delete', 'stop']
                              for service in services])
        ret['comment'] += "{0}\n".format(__salt__['cmd.run_all'](sc_cmd))

        proc_to_kill = ['msiexec.exe', 'notdpad.exe', 'cmd.exe', 'firefox.exe',
                        'iexplorer.exe', 'chrome.exe', 'powershell.exe']
        taskkill_cmd = " & ".join(["taskkill /im {0} /F".format(proc)
                                    for proc in proc_to_kill])
        ret['comment'] += "{0}\n".format(__salt__['cmd.run_all'](taskkill_cmd))

        uninstall_cmd = ('wmic product where name="{}" call uninstall '
                         '/nointeractive'.format(product))
        ret['comment'] += "{0}\n".format(__salt__['cmd.run_all'](uninstall_cmd))
    else:
        shome = home()
        if os.path.exists(shome):
            shutil.rmtree(shome)
        else:
            ret['comment'] += 'splunk is not installed at {}'.format(shome)

    ret['retcode'] = 0
    return ret


@log
def install(name,
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
            user='',
            **kwargs):
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
        stop()
        install_ret = getattr(sys.modules[__name__],
                              "_install_{t}".format(t=pkg_type))(
                          pkg=cached_pkg, splunk_home=splunk_home,
                          instances=instances, user=user, flags=install_flags)
        ret['comment'] = install_ret['comment']
        logger.info("Install runner returned code: {r}, comment: {c}".format(
                    r=install_ret['retcode'], c=install_ret['comment']))
        if install_ret['retcode'] == 0:
            if start_after_install: start()
            ret['result'] = True
            ret['changes'] = {'before': pkg_state['current_state'],
                              'after': info()}

    elif pkg_state['retcode'] == 2: # retcode = 2, pkg is installed already.
        ret['comment'] = pkg_state['comment']
        ret['result'] = True
    else: # retcode is 0, not going to install
        ret['comment'] = pkg_state['comment']
    return ret


cli = cmd
get_web_port = get_splunkweb_port
set_web_port = set_splunkweb_port


#### Internal functions ####

def _get_pkg_url(pkg, version, build='', type='splunk', pkg_released=False,
        fetcher_url='http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'):
    schemes = ['salt:', 'http:', 'https:', 'ftp:', 's3:']
    if any([True for i in schemes if pkg.startswith(i)]):
        pkg_url = pkg # pkg is set as static url
    else:
        params = {'PLAT_PKG': pkg, 'DELIVER_AS': 'url'}
        if type == 'splunkforwarder':
            params.update({'UF': '1'})
        if pkg_released:
            params.update({'VERSION': version})
        else:
            params.update({'BRANCH': version})
            if build:
                if build.isdigit():
                    params.update({'P4CHANGE': build})
                else:
                    logger.warn("build '{b}' is not a number!".format(b=build))

        r = requests.get(fetcher_url, params=params)
        if 'Error' in r.text.strip():
             raise salt.exceptions.CommandExecutionError(
                       "Fetcher returned an error: {e}, "
                       "requested url: {u}".format(
                           e=r.text.strip(), u=r.url))
        pkg_url = r.text.strip()
    return pkg_url


def _is_pkg_installed(pkg):
    """
    check if splunk is installed at desired version/build

    :param pkg:
    :return:
    """
    reg = re.search("splunk(forwarder)?-([0-9.]+)-(\d{5,7})", pkg)
    (version, build) = (reg.group(2), reg.group(3))
    if info():
        if info()['VERSION'] == version and info()['BUILD'] == build:
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

    if is_splunk_installed():
        current_pkg = info()
        ret['current_state'] = current_pkg
        ret['comment'] = "Current pkg {v}-{b} ".format(
            v=current_pkg['VERSION'], b=current_pkg['BUILD'])
        if LooseVersion(current_pkg['VERSION']) > LooseVersion(version):
            ret['retcode'] = 0
            ret['comment'] += "has higher version than '{p}'".format(p=pkg)
        elif LooseVersion(current_pkg['VERSION']) == LooseVersion(version):
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
    cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {f} {q}'.format(
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
    ret = _run_install_cmd(cmd, user)
    ret['comment'] += comment
    return ret


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


def _named_tuple_list_to_dict_list(tuple_list):
    return [dict(zip(i._fields, i)) for i in tuple_list]


def _path(path):
    """
    Get the path in splunk dir.

    :param path_: path
    :return: path in splunk dir.
    :rtype: str
    """
    return os.path.join(home(), *path.split(':'))


