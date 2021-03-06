import os
import tempfile
import logging
import random
import time
from titanium.splunk import get_splunk
from titanium.installer import InstallerFactory

INDEX_URL = "https://pypi.fury.io/m4dy9Unh83NCJdyGHkzY/beelit94/"

log = logging.getLogger(__name__)


def _random_sleep():
    '''
    to avoid heart beat failure
    '''
    m_sec = random.randint(0, 1500)
    time.sleep(m_sec / 100)


def _get_splunk(username="admin", password="changeme", login=True):
    '''
    returns the object which represents a splunk instance
    '''
    splunk = get_splunk(
        splunk_home=__salt__['grains.get']('splunk_home'),
        username=username, password=password, login=login)
    return splunk


def _get_installer(pkg_url, splunk_type, splunk_home, pkg_path=None):
    '''
    return the splunk installer object
    '''
    return InstallerFactory.create_installer(
        pkg_url, splunk_type, splunk_home, pkg_path)


def is_installed():
    '''
    check if splunk is installed or not

    :return: True if splunk is installed, else False
    :rtype: Boolean
    '''
    pkg_url = __salt__['grains.get']('pkg_url')
    pkg_path = __salt__['grains.get']('pkg_path')
    splunk_home = __salt__['grains.get']('splunk_home')
    splunk_type = __salt__['grains.get']('splunk_type')

    if splunk_home is None:
        return False

    installer = _get_installer(pkg_url, splunk_type, splunk_home, pkg_path)
    return installer.is_installed()


def install(pkg_url, type='splunk', upgrade=False, splunk_home=None):
    """
    install Splunk

    :param pkg_url: arguments which you want to pass the release fetcher
    :type pkg_url: string
    :param type: splunk, splunkforwarder or splunklite
    :type type: string
    :param upgrade: True if you want to upgrade splunk
    :type upgrade: bool
    :param splunk_home: path for splunk install to
    :type splunk_home: string
    :rtype: dict
    :return: command line result in dict ['retcode', 'stdout', 'stderr']
    """

    installer = _get_installer(pkg_url, type, splunk_home)

    if installer.is_installed() and not upgrade:
        # set grains
        log.debug('splunk is installed')
        return dict({'retcode': 9,
                     'stdout': 'splunk is installed',
                     'stderr': 'splunk is installed'})
    else:
        __salt__['grains.set']('splunk_home', installer.splunk_home)
        __salt__['grains.set']('splunk_type', type)
        __salt__['grains.set']('pkg_url', pkg_url)
        __salt__['grains.set']('pkg_path', installer.pkg_path)
        result = installer.install()
        splunk = _get_splunk(login=False)
        splunk.start()
        return result


def edit_conf_file(conf_name, stanza_name, data=None, app=None, owner=None,
                   sharing='system', do_restart=True):
    '''
    edit config file
    '''
    splunk = _get_splunk()
    splunk.edit_conf_file(
        conf_name, stanza_name, data, app, owner, sharing, do_restart)


def read_conf_file(conf_name, stanza_name=None, key_name=None, owner=None,
                   app=None, sharing='system'):
    splunk = _get_splunk()
    return splunk.read_conf_file(
        conf_name, stanza_name, key_name, owner, app, sharing)


def cli(cmd, auth=None):
    '''
    run splunk cli
    :type cmd: string
    :param cmd: cmd for splunk to execute
    :type auth: string
    :param auth: auth string for executing cmd, ex: 'admin:changeme'
                 pass None if you don't need auth string
    '''
    splunk = _get_splunk(login=False)
    return splunk.cli(cmd, auth)


def is_stanza_existed(conf_name, stanza_name, owner=None, app=None,
                      sharing='system'):
    '''
    check if a stanza is existed in the given conf file

    :type conf_name: string
    :type stanza_name: string
    :type sharing: string
    :param conf_name: name of the conf file
    :param stanza_name: name of the stanza to check
    :param owner: namespace of the conf
    :param app: namespace of the conf
    :param sharing: The scope you want the conf to be. it can be user, app,
        or system.
    :return: boolean
    '''
    splunk = _get_splunk()

    try:
        conf = splunk.confs[conf_name]
    except KeyError:
        return False
    return stanza_name in conf


def config_cluster_master(pass4SymmKey, cluster_label, replication_factor=2,
                          search_factor=2, number_of_sites=1,
                          site_replication_factor=None,
                          site_search_factor=None):
    """
    config splunk as a master of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethemaster

    :param pass4SymmKey: it's a key to communicate between indexer cluster
    :param cluster_label: the label for indexer cluster
    :param search_factor: factor of bucket be able to search
    :param replication_factor: factor of bucket be able to replicate
    """

    splunk = _get_splunk()
    splunk.config_cluster_master(
        pass4SymmKey, cluster_label, replication_factor, search_factor,
        number_of_sites, site_replication_factor, site_search_factor)


def config_cluster_slave(pass4SymmKey, cluster_label, master_uri=None,
                         replication_port=9887, site=None):
    """
    config splunk as a peer(indexer) of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethepeers

    :param pass4SymmKey: is a key to communicate between indexer cluster
    :param cluster_label: the label for indexer cluster
    :param replication_port: port to replicate data
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        indexer-cluster-master
    :param site: None if the slave is on single site, else "site1" or "site2"
    :type site: string
    """
    _random_sleep()

    if master_uri is None:
        master_uri = get_list_of_mgmt_uri('indexer-cluster-master')[0]

    splunk = _get_splunk()
    splunk.config_cluster_slave(
        pass4SymmKey, cluster_label, master_uri, replication_port, site)


def config_cluster_searchhead(pass4SymmKey, cluster_label, master_uri=None,
                              site=None):
    """
    config splunk as a search head of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail

    :param pass4SymmKey:  is a key to communicate between indexer cluster
    :param cluster_label: the label for indexer cluster
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        splunk-cluster-master
    :param site: None if the search head is on single site, else
        "site1" or "site2"...
    :type site: string
    """
    _random_sleep()

    if not master_uri:
        master_uri = get_list_of_mgmt_uri('indexer-cluster-master')[0]

    splunk = _get_splunk()
    splunk.config_cluster_searchhead(
        pass4SymmKey, cluster_label, master_uri, site)


def config_shcluster_deployer(pass4SymmKey, shcluster_label):
    '''
    config a splunk as a deployer of a search head cluster
    refer to http://docs.splunk.com/Documentation/Splunk/6.3.3/DistSearch/
    PropagateSHCconfigurationchanges#Choose_an_instance_to_be_the_deployer

    :param shcluster_label: refer to http://docs.splunk.com/Documentation/
                                            Splunk/6.3.3/DMC/Setclusterlabels
    :param pass4SymmKey: is a key to communicate between cluster
    '''
    splunk = _get_splunk()
    splunk.config_shcluster_deployer(pass4SymmKey, shcluster_label)


def config_shcluster_member(
        pass4SymmKey, shcluster_label, replication_port,
        replication_factor=None,
        conf_deploy_fetch_url=None):
    '''
    config splunk as a member of a search head cluster

    :param pass4SymmKey: pass4SymmKey for SHC
    :param shcluster_label: shcluster's label
    :param replication_port: replication port for SHC
    :param replication_factor: replication factor for SHC,
        if it's None use default provided by Splunk
    :param conf_deploy_fetch_url: deployer's mgmt uri
    '''

    if conf_deploy_fetch_url is None:
        conf_deploy_fetch_url = \
            get_list_of_mgmt_uri('search-head-cluster-deployer')[0]

    splunk = _get_splunk()
    splunk.config_shcluster_member(
        pass4SymmKey, shcluster_label, replication_port, conf_deploy_fetch_url,
        replication_factor)


def bootstrap_shcluster_captain(shc_members=None):
    '''
    bootstrap a splunk instance as a captain of a search head cluster captain

    :param shc_members: list of shc members,
        ex. https://192.168.0.2:8089,https://192.168.0.3:8089
    '''
    if shc_members is None:
        shc_members = get_list_of_mgmt_uri('search-head-cluster-member')

    splunk = _get_splunk()
    return splunk.bootstrap_shcluster_captain(shc_members)


def remove_search_peer(peers):
    '''
    remove search peer from a search head
    :type peers: list
    :param peers: ex, ['<ip>:<port>','<ip>:<port>', ...]
    '''
    # try to remove peers not in list
    # todo fix username and password
    splunk = _get_splunk()
    splunk.remove_search_peer(peers=peers)


def config_search_peer(
        peers=None, remote_username='admin', remote_password='changeme'):
    '''
    config splunk as a peer of a distributed search environment
    http://docs.splunk.com/Documentation/Splunk/latest/DistSearch/
        Configuredistributedsearch#Edit_distsearch.conf

    if a search head is part of indexer cluster search head,
    will raise EnvironmentError
    refer to http://docs.splunk.com/Documentation/Splunk/6.3.3/DistSearch/
        Connectclustersearchheadstosearchpeers#
        Search_head_cluster_with_indexer_cluster

    :param peers: list value, ex, ['<ip>:<port>','<ip>:<port>']
    :param remote_username: splunk username of the search peer
    :param remote_password: splunk password of the search peer
    :raise CommandExecutionError, if failed
    '''
    if not peers:
        peers = get_list_of_mgmt_uri('indexer')

    splunk = _get_splunk()
    splunk.config_search_peer(peers, remote_username, remote_password)


def config_deployment_client(server=None):
    '''
    config deploymeny client
    refer to http://docs.splunk.com/Documentation/Splunk/latest/Updating/
        Aboutdeploymentserver#Deployment_server_and_clusters

    deployment client is not compatible if a splunk is
    1. member of idx cluster
    2. member of search head cluster
    if role contains these will raise EnvironmentError
    :param server: mgmt uri of deployment server
    '''

    roles = __salt__['grains.get']('role')

    for role in roles:
        if role == 'indexer-cluster-peer' or \
           role == 'search-head-cluster-member':
            raise EnvironmentError(
                'Cant config deployment client for this instance')

    if not server:
        server = get_list_of_mgmt_uri('deployment-server')[0]

    splunk = _get_splunk()
    splunk.config_deployment_client(server)


def allow_remote_login():
    '''
    config allowRemoteLogin under server.conf
    '''
    splunk = _get_splunk()
    splunk.allow_remote_login()


def add_license(license_path):
    '''
    :type license_path: string
    :param license_path: where the license is. It should be start with
        'salt://'
    '''
    name = os.path.basename(license_path)
    license = __salt__['cp.get_file'](
        license_path, os.path.join(tempfile.gettempdir(), name))

    splunk = _get_splunk()
    if license is not None:
        return splunk.add_license(license)


def config_license_slave(master_uri=None):
    '''
    config splunk as a license slave

    :param master_uri: uri of the license master
    :type master_uri: string
    '''
    splunk = _get_splunk()

    if not master_uri:
        master_uri = get_list_of_mgmt_uri('central-license-master')[0]

    if not master_uri.startswith("https://"):
        master_uri = 'https://{u}'.format(u=master_uri)

    splunk.config_license_slave(master_uri)


def get_mgmt_uri(hostname=None):
    '''
    get mgmt uri of splunk

    :param hostname: the hostname to use for mgmt uri
    :type hostname: string
    :return: The mgmt uri of splunk, return None if Splunk is not started
    :rtype: string
    '''
    # todo auth parameter

    splunk = _get_splunk()
    return splunk.mgmt_uri


def get_list_of_mgmt_uri(role, raise_exception=False, retry_count=5,
                         no_scheme=False):
    '''
    :param role: grains role matched
    :type role: str
    :rtype: list
    :return: [<ip>:<port>, <ip>:<port>]
    '''

    minions = None
    while True:
        role_str = 'role:' + role
        minions = __salt__['mine.get'](
            role_str, 'splunk.get_mgmt_uri', 'grain')

        log.warn('runner returned: ' + str(minions))

        if minions and isinstance(minions, dict):
            ret = []
            for key, value in minions.iteritems():
                if no_scheme and value.startswith("https://"):
                    ret.append(value[8:])
                else:
                    ret.append(value)
            return ret

        retry_count -= 1
        if retry_count == 0:
            break

        time.sleep(5)
        log.warn('runner returned value is not valid, retrying...')

    if raise_exception:
        raise EnvironmentError(
            "Can't get the result from master: %s" % str(minions))
    else:
        return []


def uninstall():
    '''
    uninstall splunk if splunk is installed
    '''
    installer = _get_installer(
        pkg_url=__salt__['grains.get']('pkg_url'),
        splunk_type=__salt__['grains.get']('splunk_type'),
        splunk_home=__salt__['grains.get']('splunk_home'),
        pkg_path=__salt__['grains.get']('pkg_path'))
    result = installer.uninstall()

    if result:
        # delete grains
        __salt__['grains.delval']('pkg_url')
        __salt__['grains.delval']('splunk_type')
        __salt__['grains.delval']('splunk_home')
        __salt__['grains.delval']('pkg_path')
        return result
    else:
        msg = "Error when uninstalling Splunk"
        raise Exception(msg)


def create_users(username_prefix, user_count, roles):
    '''
    Create a large group of user on splunk, user and password are the same

    :param username_prefix: username_prefix, the username will be in form of
        <prefix><number>
    :param user_count: number of user to be created
    :param roles: role of user add to, could be a list or a single role
    '''
    splunk = _get_splunk()
    splunk.create_users(count=user_count, prefix=username_prefix, roles=roles)


def create_saved_searches(name_prefix, count, search, **kwargs):
    '''
    Create a batch of saved search/report/alert
    http://docs.splunk.com/Documentation/Splunk/latest/admin/Savedsearchesconf

    :param name_prefix: prefix name of saved search
    :param count: number of search is going to create
    :param kwargs: any data under a saved search stanza, ex. search="*"
    :return: None
    '''
    splunk = _get_splunk()
    splunk.create_saved_searches(
        count=count, search=search, prefix=name_prefix, **kwargs)


def enable_listen(port):
    '''
    enable listening on the splunk instance
    :param port: the port number to enable listening
    :type port: integer
    :return: None
    '''
    splunk = _get_splunk()
    splunk.enable_listen(port)

    __salt__['grains.append']("listening_ports", port)


def add_forward_server(server):
    '''
    add forward server to the splunk instance
    :param server: server to add to the splunk instance
    :type server: string
    :return: None
    '''
    splunk = _get_splunk()
    splunk.add_forward_server(server)


def add_deployment_app(name):
    '''
    '''
    splunk = _get_splunk()
    splunk.add_deployment_app(name)


def add_batch_of_deployment_apps(name_prefix, count):
    '''
    '''
    for i in range(count):
        add_deployment_app(name_prefix + str(i))


def config_dmc():
    '''
    config deployment management console by editing distsearch.conf
    '''

    searchheads = get_list_of_mgmt_uri('search-head', no_scheme=True)
    license_master = get_list_of_mgmt_uri(
        'central-license-master', no_scheme=True)
    deployer = get_list_of_mgmt_uri(
        'search-head-cluster-deployer', no_scheme=True)
    indexers = get_list_of_mgmt_uri('indexer', no_scheme=True)
    cluster_master = get_list_of_mgmt_uri(
        'indexer-cluster-master', no_scheme=True)
    deployment_server = get_list_of_mgmt_uri(
        'deployment-server', no_scheme=True)

    try:
        cluster_label = __pillar__['indexer_cluster']['cluster_label']
    except KeyError:
        cluster_label = None

    try:
        shcluster_label = __pillar__['search_head_cluster']['shcluster_label']
    except KeyError:
        shcluster_label = None

    splunk = _get_splunk()
    splunk.config_dmc(
        searchheads, deployer, indexers, cluster_master, license_master,
        deployment_server, cluster_label, shcluster_label)


def get_crash_log():
    splunk_home = __salt__['grains.get']('splunk_home')

    if not splunk_home:
        return False
    crash_file = []
    log_path = os.path.join(splunk_home, 'var', 'log', 'splunk')
    for file_name in os.listdir(log_path):
        if 'crash' in file_name:
            crash_file.append(file_name)

    return crash_file


def is_dmc_configured():
    '''
    check if dmc is configured
    '''
    splunk = _get_splunk()
    return splunk.is_dmc_configured()


def enable_js_debug_mode():
    '''
    by disabling js cache and minify js, javascript could be debugged
    by browser console
    '''
    splunk = _get_splunk()
    splunk.enable_js_debug_mode()


def get_listening_ports():
    '''
    get receiving/listened ports
    :return: list of listened ports
    '''
    try:
        # todo consider parsing 'display listen' result to get accurate result
        ports = __grains__['listening_ports']
        return ports
    except Exception as err:
        log.warn(str(err))
        return None


def get_forward_servers(role='indexer'):
    '''
    get list of forward server ports
    :param role: splunk-role
    :rtype: list
    :return: [<ip>:<port>, <ip>:<port>]
    '''
    minions = __salt__['mine.get']('role:{r}'.format(r=role),
                                   'splunk.get_listening_ports', 'grain')

    minion_ips = __salt__['mine.get']('role:{r}'.format(r=role),
                                      'network.ip_addrs', 'grain')

    if not minions:
        log.error('no minions matched forward servers')
        return None

    ret = []
    for minion, ports in minions.items():
        ret.append(str(minion_ips[minion][0]) + ':' + str(ports[0]))

    return ret


def add_log_cfg(logcfg_path='salt://log-local.cfg'):
    '''
    upload log-local.cfg
    :type logcfg_path: string
    :param logcfg_path: where the log-local.cfg is. It should be start with 'salt://'
    '''
    name = os.path.basename(logcfg_path)
    splunk_home = __salt__['grains.get']('splunk_home')
    logcfgfile = __salt__['cp.get_file'](
        logcfg_path, os.path.join(splunk_home, 'etc', name))
    return logcfgfile
