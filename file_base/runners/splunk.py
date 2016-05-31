import salt.client
import os
import yaml
import logging

log = logging.getLogger(__name__)

def management_uri_list(role=None):
    '''
    Get list of mgmt uris of the given roles
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    if role:
        role_str = 'G@role:%s' % role
    else:
        role_str = '*'

    # todo figure out how to avoid this hacky way but accelerated
    tsplk_info_path = '/home/ubuntu/tsplk_runner_info'
    if not os.path.exists(tsplk_info_path):
        log.debug(tsplk_info_path + ' is not found.')
        minions = client.cmd(role_str, 'splunk.get_mgmt_uri', expr_form='compound',
                             timeout=300)
        return minions

    result = dict()
    with open(tsplk_info_path, 'r') as f:
        minion_info = yaml.load(f)

    for minion, data in minion_info.items():
        if role in data['roles']:
            result.update({minion: data['private_ip'] + ':8089'})

    log.warn('return list value: %s' % str(result))
    return result


def get_forward_servers():
    '''
    Get the ip and listening ports on all indexers and return in list of
    <ip>:<port>
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    listening_ports = client.cmd(
        "G@role:indexer", 'grains.get', arg=['listening_ports'],
        expr_form='compound', timeout=300)
    ips = client.cmd(
        "G@role:indexer", 'grains.get', arg=['ipv4'],
        expr_form='compound', timeout=300)

    ret = []
    for key, value in ips.items():
        ip = value[-1]
        for port in listening_ports[key]:
            ret.append(ip + ":" + str(port))
    return ret