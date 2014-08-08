# -*- coding: utf-8 -*-
'''
Module for splunk instances
==========================
'''

__author__ = 'cchung'
import os
import subprocess
import time
import ConfigParser

# salt utils
import salt.utils
import salt.exceptions

__salt__ = {}
__pillar__ = {}
no_section = 'no_section'


class _FakeSecHead(object):
    '''
    Handle conf file for key-value without section.
    This piece of codes is mainly from Alex's answer here:
    http://stackoverflow.com/questions/2819696/parsing-properties-file-in-python

    the following confs might not have section (stanza):

        ui-prefs.conf
        transforms.conf
        source-classifier.conf
        segmenters.conf
        searchbnf.conf
        savedsearches.conf
        indexes.conf
        fields.conf
        eventdiscoverer.conf
        crawl.conf
        commands.conf
        alert_actions.conf
    '''
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
    ''' salt virtual '''
    if os.path.exists(get_splunk_home()):
        return True
    else:
        return False


def get_splunk_home():
    '''
    get splunk_home location
    :return: str: splunk_home
    '''
    return __salt__['pillar.get']('splunk:home')


def is_splunk_installed():
    return __virtual__()
def start():   return cmd('start')
def restart(): return cmd('restart')
def stop():    return cmd('stop')
def status():  return cmd('status')
def version(): return cmd('version')

def get_splunkd_port():
    return cmd('show splunkd-port')['stdout'].split(':')[1].strip()

def get_splunkweb_port():
    return cmd('show web-port')['stdout'].split(':')[1].strip()

def get_web_port():
    return get_splunkweb_port()

def set_splunkweb_port(port='', method='rest'):
    raise NotImplementedError

def rest_call(endpoint, ):
    raise NotImplementedError

def info():
    '''
    splunk product information, contains version, build, product, and platform
    :return: dict of product information
    '''
    if not is_splunk_installed():
        return {}
    f = open(os.path.join(splunk_path('etc'), 'splunk.version'), 'r')
    return dict([l.strip().split('=') for l in f.readlines()])


def cli(command, auth=''):
    '''
    an alias to cmd
    :param command:
    :param auth:
    :return:
    '''
    if not is_splunk_installed():
        return 'Splunk is not installed'
    return cmd(command, auth)


def cmd(command, auth='', timeout=60, wait=True):
    '''
    splunk command
    :param command:
    :param auth:
    :return:
    '''
    ret = {}
    if not is_splunk_installed():
        return 'Splunk is not installed'
    if not auth:
        auth = __salt__['pillar.get']('splunk:auth')

    cmd_ = command.split(' ')
    no_auth_cmds = ['status', 'restart', 'start', 'stop', 'version']
    if cmd_[0] in no_auth_cmds:
        if cmd_[0] == 'start':
            cmd_ += ['--accept-license', '--no-prompt', '--answer-yes']
    else:
        cmd_ += ['-auth', auth]
    p = subprocess.Popen([splunk_path('bin_splunk')]+ cmd_,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    start_time = time.time()
    time.sleep(0.5)
    if wait:
        # raise and terminate the process while timeout
        while True:
            if p.poll() == None:
                if time.time() - start_time > timeout:
                    p.kill()
                    raise salt.exceptions.CommandExecutionError((
                              "cmd not finished in {s}s".format(s=timeout)))
            else:
                break
            time.sleep(2)
        ret['stdout'], ret['stderr'] = p.communicate()
        ret['retcode'] = p.returncode
    else:
        ret['stdout'] = ''
        ret['stderr'] = 'Not waiting for command to complete'
        ret['retcode'] = p.returncode

    return ret



def add_monitor(source, index='main', wait=False, event_count=0):
    '''

    :param source:
    :param index:
    :param wait:
    :param event_count:
    :return:
    '''
    if os.path.exists(source):
        cmd("add monitor {s} index={i}".format(s=source, i=index))
    raise NotImplementedError


def massive_cmd(command, func='cmd', flags={}, parallel=False):
    '''

    :param command:
    :param func:
    :param flags:
    :param parallel:
    :return:
    '''
    raise NotImplementedError


def _read_config(conf_file):
    '''

    :param conf_file:
    :return:
    '''
    cp = ConfigParser.SafeConfigParser()
    cp.readfp(_FakeSecHead(open(conf_file, 'w+'), no_section))
    return cp


def _write_config(conf_file, cp):
    '''

    :param conf_file:
    :param cp:
    :return:
    '''
    # TODO: need to handle dummy section
    with open(conf_file, 'w+') as f:
        return cp.write(f)


def locate_conf_file(scope, conf):
    '''
    locate the conf file in specified scope.
    :param scope:
    :param conf:
    :return:
    '''
    return os.path.join(*[splunk_path('etc')] + scope.split(':') + [conf])


def edit_stanza(conf,
                stanza,
                scope='system:local',
                restart_splunk=False,
                action='edit'):
    '''
    edit a stanza from a conf, will add the stanza if it doenst exist

    :param conf: conf file, e.g.: server.conf
    :param stanza: in dict form, e.g. {'clustering': {'mode': 'master'}}
    :param scope: splunk's conf scope, delimited by colon
    :param restart_splunk: if restart splunk after set stanza.
    :param action: perform action on conf (edit, remove)
    :returns: string indicating the results
    '''
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
    '''

    :param path_:
    :return:
    '''
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
