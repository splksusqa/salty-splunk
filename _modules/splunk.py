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
    if get_splunkhome():
        return True
    else:
        return False


def get_splunkhome():
    '''

    :return: str: splunk_home
    '''
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
    return subprocess.check_output([path['bin_splunk']]+ cmd_,
                                   stderr=subprocess.STDOUT)


def _read_config(conf_file):
    ''' '''
    cp = ConfigParser.SafeConfigParser()
    cp.readfp(_FakeSecHead(open(conf_file, 'w+'), no_section))
    return cp


def _write_config(conf_file, cp):
    ''' '''
    # TODO: need to handle dummy section
    with open(conf_file, 'w+') as f:
        return cp.write(f)


def locate_conf_file(scope, conf):
    ''' locate the conf file in specified scope.'''
    return os.path.join(*[path['etc']] + scope.split(':') + [conf])


def edit_stanza(conf,
                stanza,
                scope='system:local',
                restart_splunk=False,
                action='edit'):
    '''
    edit a stanza from conf, will add the stanza if it doenst exist
    :param conf: file, e.g.: server.conf
    :param stanza: stanza in dict form, e.g. {'clustering': {'mode': 'master'}}
    '''
    if not action.strip() in ['edit', 'add', 'remove', 'delete']:
        return "Unknown action '{a}' for editing stanza".format(a=action)
    conf_file = locate_conf_file(scope, conf)
    cp = _read_config(conf_file)

    # edit the whole stanza if it's a string
    if type(stanza) == str:
        if action.strip() in ['edit', 'add']:
            if not stanza in cp.sections():
                cp.add_section(stanza)
        else:
            if stanza in cp.sections():
                cp.remove_section(stanza)


    # edit the key value if stanza is dict.
    elif type(stanza) == dict:
        for s, kv in stanza.iteritems():
            if action.strip() in ['edit', 'add']:
                if not s in cp.sections():
                    cp.add_section(s)
            else:
                if not s in cp.sections():
                    return ("Stanza to remove {s} not exist, skipping".format(
                             s=s))

            if type(kv) == dict:
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

    # if not stanza in cp.sections():
    #     cp.add_section(stanza)
    # for k,v in kv.items():
    #     cp.set(stanza, k, v)
    try:
        _write_config(conf_file, cp)
        if restart_splunk:
            restart()
        return "Successfully updated stanza {s} for conf {c}".format(
                   s=stanza, c=conf)
    except Exception as e:
        return "Failed to update conf {c}, exception: {e}".format(c=conf, e=e)


#
# def set_role(mode, **kwargs):
#     if mode.startswith('cluster'):
#         if mode == 'cluster-master':
#             conf = {'mode': 'master'}
#         elif mode in ['cluster-searchhead', 'cluster-slave']:
#             conf = {'mode': 'slave', 'master_uri': kwargs.get('master')}
#         else:
#             raise salt.execptions.CommandExecutionError(
#                       "Role '{r}' isn't supported".format(r=mode))
#         edit_stanza('server.conf', conf, 'clustering')


HOME = get_splunkhome()
no_section = 'no_section'

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
