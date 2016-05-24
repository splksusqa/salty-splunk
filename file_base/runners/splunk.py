import salt.client
import os
import yaml

def management_uri_list(role=None):
    '''
    Print a list of all of the minions that are up
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    if role:
        role_str = 'G@role:%s' % role
    else:
        role_str = '*'

    # todo figure out how to avoid this hacky way but accelerated
    tsplk_info_path = '/home/ubuntu/tsplk_runner_info'
    if not os.path.exists(tsplk_info_path):
        minions = client.cmd(role_str, 'splunk.get_mgmt_uri', expr_form='compound',
                             timeout=300)
        return minions

    result = dict()
    with open(tsplk_info_path, 'r') as f:
        minion_info = yaml.load(f)

    for minion, data in minion_info:
        if role in data['roles']:
            result.update({minion: data['private_ip'] + ':8089'})

    return result