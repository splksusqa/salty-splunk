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
        ret['comment'] = "Splunk was not installed: {s}".format(s=ret['stderr'])
    return ret

def cluster_master_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.config_cluster_master'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Splunk was configured as cluster master successfully"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
    return ret

def cluster_slave_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.config_cluster_slave'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Splunk was configured as cluster slave successfully"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
    return ret

def cluster_searchhead_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.config_cluster_searchhead'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Splunk was configured as cluster SH successfully"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
    return ret

def shcluster_deployer_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.config_shcluster_deployer'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Splunk was configured as SHC deployer successfully"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
    return ret

def shcluster_member_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.config_shcluster_member'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Splunk was configured as SHC member successfully"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
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

    config_result = __salt__['splunk.config_search_peer'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Search peer was configured successfully"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
    return ret

def deployment_client_configured(name, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.config_deployment_client'](**kwargs)

    if 0 == config_result['retcode']:
        ret['result'] = True
        ret['comment'] = "deploymeny client was configured successfully"
        ret['changes'] = {'new': "installed"}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong: {s}".format(
            s=config_result['stderr'])
    return ret

def remote_login_allowed(name, **kwargs):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    config_result = __salt__['splunk.allow_remote_login'](**kwargs)

    if 200 == config_result['status']:
        ret['result'] = True
        ret['comment'] = "Remote login was set to always"
        ret['changes'] = {"new": 'configured'}
    else:
        ret['result'] = False
        ret['comment'] = "Something went wrong. Reason: {r}".format(
            r=config_result['reason'])
    return ret
