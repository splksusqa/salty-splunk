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

    log.debug(str(result))

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

    log.warn('wait for vm {v}'.format(v=vm_count))

    if vm_count != 0:
        runner = salt.runner.RunnerClient(opts)
        runner.cmd('state.event', arg=['salt/minion/*/start'],
                   kwarg={'quiet': True, 'count': vm_count})

    return result


def create_site():
    client = salt.client.LocalClient()
    runner = salt.runner.RunnerClient(opts)

    # join to domain
    runner.cmd('splunk.join_ad_domain')

    # from pillar list
    pillar = runner.cmd('pillar.show_pillar', [])
    try:
        sites = pillar['sites']
        _set_grains(client, sites)
    except KeyError:
        pass

    try:
        sites = pillar['roles_array_site']

        len(sites)
    except KeyError:
        pass

    result = runner.cmd('state.orch', arg=['orchestration.splunk'])

    # check result


    return True


def destroy_site():
    client = salt.client.LocalClient()

    result = client.cmd('*', 'splunk.uninstall')
    log.warn(result)

    # clean up shared storage
    share_name = 'shp_share'
    result = client.cmd('role:search-head-pooling-shared-storage',
                        'cmd.run',
                        arg=['net share %s /delete' % share_name],
                        expr_form='grain')
    log.warn(result)
    result = client.cmd('role:search-head-pooling-shared-storage',
                        'file.remove',
                        arg=['C:\\shp_share'],
                        expr_form='grain')
    log.warn(result)


def _set_grains(client, sites):
    # check all minion is connected
    for site, site_data in sites.items():
        for minion, minion_data in site.items():
            result = client.cmd(minion, 'test.ping')
            if not result['ret']:
                raise EnvironmentError('{m} is not up'.format(m=minion))

    # set grains
    for site, site_data in sites.items():
        for minion, minion_data in site.items():
            result = client.cmd(minion, 'grains.set',
                                arg=['role', minion_data['role']],
                                kwarg={'force': True})
            if not result['ret']:
                raise EnvironmentError(
                    '{m} is fail to set grains'.format(m=minion))
