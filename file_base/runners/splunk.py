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

def get_forward_servers():
    '''
    Print a list of all of the minions that are up
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    listening_ports = client.cmd(
        "G@role:indexer", 'grains.get', 'listening_ports',
        expr_form='compound', timeout=300)
    ips = client.cmd(
        "G@role:indexer", 'grains.get', 'ipv4',
        expr_form='compound', timeout=300)

    ret = []
    for key, value in ips.items():
        ip = value[-1]
        for port in listening_ports[key]:
            ret.append(ip + ":" + port)
    return minions