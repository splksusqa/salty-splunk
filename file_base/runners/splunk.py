import salt.client
import salt.runner
import salt.config
import logging

log = logging.getLogger(__name__)
opts = salt.config.master_config('/etc/salt/master')
runner = salt.runner.RunnerClient(opts)
client = salt.client.LocalClient()


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
    pillar = runner.cmd('pillar.show_pillar', [])

    if 'win_domain' not in pillar:
        log.warn('domain data is not in pillar, skip joining domain')
        return None

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
        runner.cmd('state.event', arg=['salt/minion/*/start'],
                   kwarg={'quiet': True, 'count': vm_count})

    return result


def create_site():
    _clear_grains()

    # join to domain
    runner.cmd('splunk.join_ad_domain')
    # from pillar list
    pillar = runner.cmd('pillar.show_pillar', [])
    try:
        sites = pillar['sites']
        _set_grains(sites)
    except KeyError:
        pass

    try:
        sites = pillar['roles_array_site']
        # calculate the site machine
        vm_number = 0
        for site in sites:
            vm_number += len(site)

        connected_minions = runner.cmd('manage.up')
        if vm_number >= len(connected_minions):
            raise OverflowError("Can't accept more than connected VM")

        sites_with_minion_names = dict()
        _assign_roles_to_minions(connected_minions, sites,
                                 sites_with_minion_names)

        _set_grains(sites_with_minion_names)
    except KeyError:
        pass

    result = runner.cmd('state.orch', arg=['orchestration.splunk'])

    # todo check result
    return result


def _assign_roles_to_minions(connected_minions, sites, sites_with_minion_names):
    for site in sites:
        while len(site) != 0:
            minion_roles = site.pop()
            minion = connected_minions.pop()
            sites_with_minion_names.update({minion: minion_roles})


def destroy_site():
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


def _set_grains(sites):
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


def _clear_grains():
    client.cmd('*', 'grains.set', arg=['role', []])