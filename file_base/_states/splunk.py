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
