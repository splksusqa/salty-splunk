import salt.client
import salt.runner
import salt.config
import logging
from salt.utils.odict import OrderedDict

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


def get_minions_with_empty_roles():
    result = client.cmd('*', 'grains.get', arg=['role'])
    minions = []
    for minion, data in result.items():
        if not data:
            minions.append(minion)

    return minions


def create_site():
    # join to domain
    runner.cmd('splunk.join_ad_domain')
    # from pillar list
    pillar = runner.cmd('pillar.show_pillar', [])
    if 'sites' in pillar:
        _clear_grains()

        sites = pillar['sites']
        for site, site_data in sites.items():
            if isinstance(site_data, dict):
                _set_grains(site_data)
            elif isinstance(site_data, list):
                minions = _check_number_of_minions(site, site_data)
                minions_data = _assign_roles_to_minions(minions, site_data)
                _set_grains(minions_data)
            else:
                raise TypeError('sites data should be either dict or array')
    else:
        log.warn('no site data, run orchestration directly')

    result = runner.cmd('state.orch', arg=['orchestration.splunk'])

    # todo check result
    return result


def _check_number_of_minions(site, site_data):
    minions = runner.cmd('splunk.get_minions_with_empty_roles')
    if len(site_data) > minions:
        raise ValueError('{s} site has more number of roles '
                         'than available minions'.format(s=site))
    return minions


def _assign_roles_to_minions(connected_minions, site):
    sites_with_minion_names = dict()
    for roles_data in site:
        minion = connected_minions.pop()
        sites_with_minion_names.update({minion: roles_data})

    return sites_with_minion_names


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


def _set_grains(site):
    # set grains
    for minion, grains_data in site.items():
        for key, value in grains_data.items():
            result = client.cmd(minion, 'grains.set', arg=[key, value])
            if not result['result']:
                log.error(str(result))
                raise EnvironmentError(
                    '{m} is fail to set grains'.format(m=minion))


def _clear_grains():
    client.cmd('*', 'grains.set', arg=['role', []])