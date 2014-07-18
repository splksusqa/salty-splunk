# -*- coding: utf-8 -*-
'''
Module for splunk instances
==========================
'''

__author__ = 'cchung'
import os
import subprocess
import platform
import ConfigParser

# salt utils
import salt.utils
import salt.execptions


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
    def __init__(self, fp, sechead=dummy_section):
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


def __virtual__(splunk_home=''):
    ''' salt virtual '''
    if not splunk_home:
        splunk_home = get_splunkhome()
    return True


def get_splunkhome():
    if platform.system() == 'Windows':
        default = ur'C:\Program Files\Splunk'
    else:
        default = '/opt/splunk'
    #return __pillar__.get(splunk_home, {'splunk_home': default})
    return default


def start():   return cmd('start')
def restart(): return cmd('restart')
def stop():    return cmd('stop')
def status():  return cmd('status')
def version(): return cmd('version')


def cli(command, auth='admin:changeme'):
    ''' an alias to cmd '''
    return cmd(command, auth)


def cmd(command, auth='admin:changeme'):
    ''' splunk command '''
    cmd_ = command.split(' ')
    no_auth_cmds = ['status', 'restart', 'start', 'stop', 'version']
    if cmd_[0] in no_auth_cmds:
        if cmd_[0] == 'start':
            cmd_ += ['--accept-license', '--no-prompt', '--answer-yes']
    else:
        cmd_ += ['-auth', auth]
    return subprocess.check_output([path['bin_splunk']]+ cmd_)


def _read_config(conf_file):
    ''' '''
    cp = ConfigParser.SafeConfigParser()
    cp.readfp(_FakeSecHead(open(conf_file)))
    return cp


def _write_config(conf_file, cp):
    ''' '''
    # TODO: need to handle dummy section
    with open(conf_file, 'w+') as f:
        return cp.write(f)


def locate_conf_file(scope, conf):
    ''' locate the conf file in specified scope.'''
    return os.path.join(*[path['etc']] + scope.split(':') + [conf])


def edit_stanza(conf, kv, stanza='', scope='system:local'):
    ''' edit a stanza from conf, will add the stanza if it doenst exist '''
    conf_file = locate_conf_file(scope, conf)
    cp = _read_config(conf_file)
    if not stanza in cp.sections():
        cp.add_section(stanza)
    for k,v in kv.items():
        cp.set(stanza, k, v)
    return _write_config(conf_file, cp)


def remove_stanza(conf, key='', stanza='', scope='system:local'):
    '''
    remove a stanza or key-value from a conf
    to remove a stanza, just leave key as empty
    '''
    conf_file = locate_conf_file(scope, conf)
    cp = _read_config(conf_file)
    if not key:
        cp.remove_section(stanza)
    else:
        cp.remove_option(stanza, key)
    return _write_config(conf_file, cp)


def set_role(mode, **kwargs):
    if mode.startswith('cluster'):
        if mode == 'cluster-master':
            conf = {'mode': 'master'}
        elif mode in ['cluster-searchhead', 'cluster-slave']:
            conf = {'mode': 'slave', 'master_uri': kwargs.get('master')}
        else:
            raise salt.execptions.
        edit_stanza('server.conf', conf, 'clustering')


HOME = get_splunkhome()
dummy_section = 'undefined_section'


path = {
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


# conf = {
#     'system': {
#         'local':   os.path.join(path['system'], 'local'),
#         'default': os.path.join(path['system'], 'default')
#     },
#     'apps_search': {
#         'local':   os.path.join(path['apps_search'], 'local'),
#         'default': os.path.join(path['apps_search'], 'default')
#     }
# }
