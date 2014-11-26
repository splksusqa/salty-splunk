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
    splunk_home = __pillar__['splunk']['home']
    logger.info("Getting splunk_home '{h}' from pillar".format(h=splunk_home))
    return splunk_home


def is_splunk_installed():
    """
    Check if splunk is installed at splunk_home.

    :return: True if splunk_home path exists, otherwise False.
    :rtype: bool
    """
    splunk_home = home()
    if os.path.exists(_path('bin')):
        logger.info("Splunk is installed at '{h}'".format(h=splunk_home))
        return True
    else:
        logger.info("Splunk is not installed at '{h}'".format(h=splunk_home))
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


def stop(force=False):
    """
    Stop splunk, wrapped to cmd.

    :return: results of calling cmd
    """
    cmd_ = 'stop'
    if force: cmd_ += ' -f'
    return cmd(cmd_)


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
    return cmd('version')


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


def get_mgmt_uri():
    """
    Get splunk mgmt uri
    :return: splunk mgmt uri
    :rtype: str
    """
    return 'https://' + socket.gethostname().strip() + ':' + get_splunkd_port()


def listen_port(port, type='splunktcp', params=None):
    """

    :param port:
    :param type:
    :return:
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
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


def info():
    """
    splunk product information, contains version, build, product, and platform

    :return: splunk.version contents
    :rtype: dict
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    if not is_splunk_installed():
        return {}
    f = open(os.path.join(_path('etc'), 'splunk.version'), 'r')
    return dict([l.strip().split('=') for l in f.readlines()])


def install_app(source, dest='', method='cli', **kwargs):
    """

    :param app:
    :param method:
    :param kwargs:
    :return:
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    if method == 'cli':
        source = __salt__['utils.cache_file'](source=source, dest=dest)
        cmd_ = "install app {s}".format(s=source)
        return cmd(cmd_, **kwargs)
    elif method == 'rest':
        if not source.startswith('http'):
            source = __salt__['utils.cache_file'](source=source, dest=dest)
        appinstall_uri = '/services/apps/appinstall'
        return rest_call(uri=appinstall_uri, method='post',
                         body={'name': source}, **kwargs)
    else:
        return "Install app method {m} is not supported".format(m=method)


def add_monitor(source, dest='', index='', wait=False, event_count=0,
                params=None):
    """

    :param source:
    :param index:
    :param wait:
    :param event_count:
    :return:
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
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


def _wait_until_indexing_stable(index, event_count=0, source='', sourcetype=''):
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    raise NotImplementedError


def massive_cmd(command, func='cmd', flags='', parallel=False):
    """

    :param command:
    :param func:
    :param flags:
    :param parallel:
    :return:
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    raise NotImplementedError


def multi_instances(func):
    def multi(**kwargs):
        instances = __pillar__['splunk']['instances']
        splunk_home_base = kwargs.get('home')
        splunk_port_base = kwargs.get('port')
        ret = {}
        for i in xrange(0, instances):
            kwargs.update({
                'splunk_home': splunk_home_base + '_' + str(i),
                'port': int(splunk_port_base) + i
            })
            ret.update({ splunk_home_base + '_' + str(i): func(**kwargs)})
        return ret
    return multi


# @multi_instances
def cmd(command, auth='', user='', timeout=60, params=None, **kwargs):
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
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
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
    msg = ("Ran splunk cmd '{cmd}' at '{cwd}', retcode={retcode}\n"
           "stdout:\n{stdout}\nstderr:\n{stderr}".format(**ret))
    logger.info(msg)
    return ret


# @multi_instances
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
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
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
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))

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
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    # handle unicode endings, SQA-420
    content = open(conf_file).read()
    for e in [r'\xfe\xff', r'\xff\xfe', r'\xef\xbb\xbf']:
        content = re.sub(e, '', content)
    open(conf_file, 'w').write(content)
    # read as ConfigParser (cp)
    cp = ConfigParser.SafeConfigParser()
    cp.optionxform = str
    cp.readfp(_FakeSecHead(open(conf_file, 'a+'), default_stanza))
    return cp


def _write_config(conf_file, cp):
    """
    Write the configurations in ConfigParser into conf file.

    :param str conf_file: string of the conf file path.
    :param obj cp: ConfigParser.SafeConfigParser()
    :return: ConfigParser
    :rtype: object
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
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
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    return os.path.join(*[_path('etc')] + scope.split(':') + [conf])


def get_file(source, dest=''):
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
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    return __salt__['utils.cache_file'](source=source, dest=_path(dest))


def push_file(source):
    """
    Push a file inside splunk up to salt-master, and save it to cachedir of
    salt-master, source format is dir:sub_dir_1:sub_dir_2:filename,
    cachedir default is /var/cache/salt/master/minions/minion-id/files/

    :param source: file path inside splunk home.
    :return: if the file is successfully pushed to salt-master
    :rtype: bool
    """
    logger.info("Running function '{f}' with vars: {v}".format(
                f=inspect.stack()[0][3], v=locals()))
    return __salt__['cp.push'](_path(source))


def check_log(type='crash'):
    raise NotImplementedError


def check_crash():
    raise NotImplementedError


def check_errors(logfile='', allowed=5):
    raise NotImplementedError


def event_count(host=None, source=None, sourcetype=None):
    raise NotImplementedError


def total_event_count(index='main', method='rest'):
    if method == 'rest':
        uri = "services/data/indexes/{idx}".format(idx=index)
        count = rest_call(uri, show_content=True
                    )['content']['entry'][0]['content']['totalEventCount']
    elif method == 'file':
        raise NotImplementedError
    else:
        raise NotImplementedError

    return count


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


def perf(verbose=False):
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


def _get_perf_metrics(pid, verbose):
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


def uninstall():
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
    if salt.utils.is_windows():
        sc_cmd = " & ".join(["sc {0} {1}".format(action, service)
                              for action in ['stop', 'delete', 'stop']
                              for service in ['splunkd', 'splunkweb']])
        ret['comment'] += "{0}\n".format(__salt__['cmd.run_all'](sc_cmd))

        proc_to_kill = ['msiexec.exe', 'notdpad.exe', 'cmd.exe', 'firefox.exe',
                        'iexplorer.exe', 'chrome.exe', 'powershell.exe']
        taskkill_cmd = " & ".join(["taskkill /im {0} /F".format(proc)
                                    for proc in proc_to_kill])
        ret['comment'] += "{0}\n".format(__salt__['cmd.run_all'](taskkill_cmd))

        uninstall_cmd = ('wmic product where name="splunk" call uninstall '
                         '/nointeractive')
        ret['comment'] += "{0}\n".format(__salt__['cmd.run_all'](uninstall_cmd))
    else:
        shutil.rmtree(home())

    # TODO: reload modules to make splunk module unavailable after purge.
    return ret


cli = cmd
get_web_port = get_splunkweb_port
set_web_port = set_splunkweb_port

rest_endpoints = {
    'indexes': 'servicesNS/nobody/_cluster/data/indexes/'
}
