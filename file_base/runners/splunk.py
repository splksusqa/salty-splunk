import salt.client
import salt.runner
import salt.config
import logging

log = logging.getLogger(__name__)

opts = salt.config.master_config('/etc/salt/master')


def get_forward_servers():
    '''
    Get the ip and listening ports on all indexers and return in list of
    <ip>:<port>
    '''
    client = salt.client.LocalClient()
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


def join_ad_domain():
    '''
    join all windows minion to AD domain
    :return:
    '''

    client = salt.client.LocalClient()

    result = client.cmd('os:Windows', 'state.apply',
                        arg=['splunk.windows_domain_member'],
                        expr_form='grain')

    log.error(str(result))

    is_minion_failed = False
    for minion, states in result.items():
        for state, state_result in states.items():
            if not state_result['result']:
                is_minion_failed = True
                break

    if is_minion_failed:
        return result

    # wait for minion back online
    vm_count = len(result)

    # skip if already configured
    state_str = 'module_|-join-domain_|-system.join_domain_|-run'
    for minion, states in result.items():
        if 'already' in str(states[state_str]['changes']['ret']).lower():
            vm_count -= 1

    log.error('wait for vm {v}'.format(v=vm_count))

    runner = salt.runner.RunnerClient(opts)
    runner.cmd('state.event', arg=['salt/minion/*/start'],
               kwarg={'quiet': True, 'count': vm_count})

    return result


def create_site_from_pillar():
    client = salt.client.LocalClient()
