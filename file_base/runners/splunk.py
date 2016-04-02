import salt.client


def management_uri_list(role=None):
    '''
    Print a list of all of the minions that are up
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    if role:
        role_str = 'G@role:%s' % role
    else:
        role_str = '*'
    minions = client.cmd(role_str, 'splunk.get_mgmt_uri', expr_form='compound',
                         timeout=300)

    return minions