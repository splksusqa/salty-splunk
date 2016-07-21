import logging
import os

log = logging.getLogger(__name__)


def installed(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    if __salt__['splunk.is_installed']():
        ret['comment'] = 'Splunk is already installed.'
        return ret

    installed_result = __salt__['splunk.install'](**kwargs)

    if 0 == installed_result['retcode']:
        ret['result'] = True
        ret['comment'] = "Splunk was installed successfully"
        ret['changes'] = {'new': "installed"}
    else:
        ret['result'] = False
        ret['comment'] = "Splunk was not installed: {s}".format(
            s=installed_result['stderr'])
    return ret


def configured(name, conf_name, stanza_name, data=None, do_restart=True,
               app=None, owner=None, sharing='system'):
    '''
    config splunk conf file
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    key_to_changed = []
    if data:
        for key, value in data.items():
            current_value = __salt__['splunk.read_conf'](
                conf_name, stanza_name, key)
            if str(current_value) != str(value):
                key_to_changed.append(key)

    if not key_to_changed:
        ret['result'] = True
        ret['comment'] = 'no config changed'
        return ret

    new_data = dict()
    for key in key_to_changed:
        new_data[key] = data[key]

    try:
        __salt__['splunk.config_conf'](conf_name, stanza_name, new_data,
                                       do_restart, app, owner, sharing)
        ret['result'] = True
        ret['comment'] = 'config changed successfully'
        ret['changes'] = {
            'stanza': stanza_name,
            'data': new_data
        }
    except EnvironmentError as err:
        ret['result'] = False
        ret['comment'] = str(err)

    return ret


def cluster_master_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_cluster_master'](**kwargs)
        ret['result'] = True
        ret['comment'] = "Splunk was configured as cluster master successfully"
        ret['changes'] = {"new": 'configured'}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=str(err))
    return ret


def cluster_slave_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_cluster_slave'](**kwargs)
        ret['result'] = True
        ret['comment'] = "Splunk was configured as cluster slave successfully"
        ret['changes'] = {"new": 'configured'}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=str(err))
    return ret


def cluster_searchhead_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_cluster_searchhead'](**kwargs)
        ret['result'] = True
        ret['comment'] = "Splunk was configured as cluster SH successfully"
        ret['changes'] = {"new": 'configured'}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=str(err))
    return ret


def shcluster_deployer_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_shcluster_deployer'](**kwargs)
        ret['result'] = True
        ret['comment'] = "Splunk was configured as SHC deployer successfully"
        ret['changes'] = {"new": 'configured'}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(r=str(err))
    return ret


def shcluster_member_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_shcluster_member'](**kwargs)
        ret['result'] = True
        ret['comment'] = "Splunk was configured as SHC member successfully"
        ret['changes'] = {"new": 'configured'}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(r=str(err))
    return ret


def shcluster_captain_bootstrapped(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    bootstrap_result = __salt__['splunk.bootstrap_shcluster_captain'](**kwargs)

    if 0 == bootstrap_result['retcode']:
        ret['result'] = True
        ret['comment'] = "SHC captain was bootstrapped successfully"
        ret['changes'] = {'new': "installed"}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(
            s=bootstrap_result['stderr'])
    return ret


def search_peer_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    servers_need_to_be_added = __salt__['splunk.get_list_of_mgmt_uri'](
        'indexer')

    # read current servers is configured
    current_servers = __salt__['splunk.read_conf'](
        'distsearch', 'distributedSearch', key_name='servers')
    servers_need_to_be_removed = []
    if current_servers:
        current_servers = current_servers.split(',')
        servers_need_to_be_removed = \
            set(current_servers) - set(servers_need_to_be_added)
        servers_need_to_be_added = \
            set(servers_need_to_be_added) - set(current_servers)

    log.debug('servers need to be removed %s' % str(servers_need_to_be_removed))
    log.debug('sever need to be added %s' % str(servers_need_to_be_added))

    if not servers_need_to_be_added and not servers_need_to_be_removed:
        ret['result'] = True
        ret['comment'] = "Search peer is already configured"
        return ret

    try:
        __salt__['splunk.remove_search_peer'](servers_need_to_be_removed)
        __salt__['splunk.config_search_peer'](servers_need_to_be_added)
        ret['result'] = True
        ret['comment'] = "Search peer was configured successfully"
        ret['changes'] = {"new": 'indexer added %s \n indexer removed %s' % (
            str(servers_need_to_be_added), str(servers_need_to_be_removed))}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(r=str(err))
    return ret


def deployment_client_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_deployment_client'](**kwargs)
        ret['result'] = True
        ret['comment'] = "deploymeny client was configured successfully"
        ret['changes'] = {'new': "installed"}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(s=str(err))
    return ret


def license_client_configured(name, **kwargs):
    '''

    :param name:
    :param kwargs:
    :return:
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.config_license_slave'](**kwargs)
        ret['result'] = True
        ret['comment'] = "configured as a license slave"
        ret['changes'] = {'new': "configured as a license slave"}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(s=str(err))
    return ret


def license_added(name, **kwargs):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        __salt__['splunk.add_license'](**kwargs)
        ret['result'] = True
        ret['comment'] = "configured as a license master"
        ret['changes'] = {'new': "license added"}
    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(s=str(err))
    return ret


def forward_servers_added(name, servers=None):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    servers = __salt__['publish.runner']('splunk.get_forward_servers') \
        if servers is None else servers
    try:
        servers = [servers, ] if type(servers) is not list else servers
        for server in servers:
            # if the server is added already, skip
            stanza = "tcpout-server://{s}".format(s=server)
            if not __salt__['splunk.is_stanza_existed']('outputs', stanza):
                __salt__['splunk.add_forward_server'](server)

        ret['result'] = True
        ret['comment'] = "{s} have been added as forward-server" \
            .format(s=str(servers))
        ret['changes'] = {'new': servers}

    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(s=str(err))
    return ret


def listening_ports_enabled(name, ports):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}
    ports = [ports, ] if type(ports) is not list else ports

    try:
        for port in ports:
            stanza = "splunktcp://{p}".format(p=port)
            existed = __salt__['splunk.is_stanza_existed'](
                'inputs', stanza, owner='admin', app='search', sharing='user')
            if not existed:
                __salt__['splunk.enable_listen'](port)
        ret['result'] = True
        ret['comment'] = "{p} have been enabled as listening port" \
            .format(p=str(ports))
        ret['changes'] = {'new': ports}

    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(s=str(err))
    return ret


def config_dmc(name):
    '''
    config dmc
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    try:
        if __salt__['splunk.is_dmc_configured']():
            ret['result'] = True
            ret['comment'] = "dmc is already configured, nothing changed"
        else:
            __salt__['splunk.config_dmc']()
            ret['result'] = True
            ret['comment'] = "dmc has been configured on this instance"
            ret['changes'] = {'new': "dmc is configured"}

    except Exception as err:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(s=str(err))
    return ret


def create_shared_folder(name, shared_name, folder_path):
    '''
    create share folder on windows for shp, windows only
    :param name: name of id
    :param shared_name: name of share folder
    :param folder_path: folder to be shared
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    cmd = r'net share {s}="{f}" "/GRANT:EVERYONE,Full"'.format(
        s=shared_name, f=os.path.normpath(folder_path))
    result = __salt__['cmd.run_all'](cmd=cmd, python_shell=True)

    if result['retcode'] == 2 and ('already' in result['stderr']):
        ret['comment'] = result['stderr']
        return ret

    if result['retcode'] == 0:
        ret['changes'] = {'new': '{s} is shared'.format(s=shared_name)}
    else:
        ret['result'] = False
        ret['comment'] = result['stdout'] + result['stderr']

    return ret


def copy_shp_shared_files(name, splunk_home, shared_folder_path,
                          runas, password):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    shared_folder_path = os.path.normpath(shared_folder_path)
    folders = ['users', 'apps']

    for f in folders:
        from_folder = os.path.join(splunk_home, 'etc', f)
        to_folder = os.path.join(shared_folder_path, 'etc', f)

        cmd = r' robocopy "{f}" "{t}" /e /xo /NFL /NDL'.format(
            h=splunk_home, t=to_folder, f=from_folder)

        result = __salt__['cmd.run_all'](cmd, runas=runas, password=password)

        # ref http://ss64.com/nt/robocopy-exit.html
        if result['retcode'] > 7:
            ret['result'] = False
            ret['comment'] = result['stdout'] + result['stderr']
            return ret
        else:
            ret['changes'] = {
                'new': 'files copied'
            }
            ret['comment'] += (result['stdout'] + result['stderr'])

    return ret


def enable_search_head_pooling(name, shared_folder):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    pooling_status = __salt__['splunk.cli']('pooling display')

    if 'enabled' in pooling_status['stdout']:
        ret['comment'] = 'pooling is already enabled'
        return ret

    # deal with windows path
    shared_folder = os.path.normpath(shared_folder)
    result = __salt__['splunk.cli'](
        r'pooling enable {s}'.format(s=shared_folder))

    if result['retcode'] != 0:
        ret['result'] = False
        ret['comment'] = result['stdout'] + result['stderr']
        return ret

    ret['changes'] = {'new': 'pooling enabled'}
    ret['comment'] = result['stdout']
    return ret
