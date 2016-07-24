import requests
import os
import tempfile
import sys
import logging
import re
from salt.exceptions import CommandExecutionError
import random
import time

PLATFORM = sys.platform
FETCHER_URL = 'http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'
log = logging.getLogger(__name__)


def _is_windows():
    if 'win' in sys.platform:
        return True
    else:
        return False

def _import_sdk():
    try:
        import splunklib
    except ImportError:
        if "win" in PLATFORM:
            __salt__['pip.install'](
                pkgs='splunk-sdk',
                bin_env='C:\\salt\\bin\\Scripts\\pip.exe',
                cwd="C:\\salt\\bin\\scripts")
        else:
            __salt__['pip.install']('splunk-sdk')
        import splunklib
    return splunklib


def _random_sleep():
    '''
    to avoid heart beat failure
    '''
    m_sec = random.randint(0, 1500)
    time.sleep(m_sec / 100)


def _get_splunk(username="admin", password="changeme", owner=None, app=None,
                sharing='system'):
    '''
    returns the object which represents a splunk instance
    '''
    splunklib = _import_sdk()
    import splunklib.client as client

    splunk = client.connect(
        username=username, password=password, sharing=sharing, owner=owner,
        app=app, autologin=True)
    return splunk


def cli(command):
    '''
    run splunk cli
    :param command: splunk cli command
    '''
    installer = InstallerFactory.create_installer()
    splunk_home = installer.splunk_home
    cmd = '"{p}" {c}'.format(p=os.path.join(splunk_home, 'bin', 'splunk'),
                             c=command)

    domain_name = __salt__['pillar.get']('win_domain:domain_name', default=None)

    if domain_name:
        password = __salt__['pillar.get']('win_domain:password', default=None)
        user = __salt__['pillar.get']('win_domain:username', default=None)
        runas = domain_name + '\\' + user
    else:
        runas = None
        password = None

    if runas and password and _is_windows():
        return __salt__['cmd.run_all'](cmd, runas=runas, password=password)
    else:
        return __salt__['cmd.run_all'](cmd)


class InstallerFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def create_installer(splunk_type=None):
        if "linux" in PLATFORM:
            installer = LinuxTgzInstaller(splunk_type)
        elif "win" in PLATFORM:
            installer = WindowsMsiInstaller(splunk_type)
        else:
            # to do: throw error when platform is not supported
            raise NotImplementedError
        return installer


class Installer(object):
    def __init__(self, splunk_type=None):
        if not self.splunk_type:
            self.splunk_type = splunk_type

    def install(self, pkg_path, splunk_home=None, **kwargs):
        pass

    def is_installed(self):
        pass

    def uninstall(self):
        pass

    @property
    def pkg_path(self):
        ''' where the package file is stored'''
        return __salt__['grains.get']('pkg_path')

    @pkg_path.setter
    def pkg_path(self, value):
        __salt__['grains.set']('pkg_path', value, force=True)

    @property
    def splunk_home(self):
        grains_value = __salt__['grains.get']('splunk_home')
        if grains_value:
            return grains_value

        return None

    @splunk_home.setter
    def splunk_home(self, value):
        __salt__['grains.set']('splunk_home', value, force=True)

    @property
    def splunk_type(self):
        ''' splunk types are: splunk, splunkforwarder, or splunklight'''
        splunk_type = __salt__['grains.get']('splunk_type')
        return splunk_type if splunk_type else None

    @splunk_type.setter
    def splunk_type(self, value):
        __salt__['grains.set']('splunk_type', value, force=True)


class WindowsMsiInstaller(Installer):
    def __init__(self, splunk_type):
        super(WindowsMsiInstaller, self).__init__(splunk_type)
        if not self.splunk_home:
            self.splunk_home = "C:\\Program Files\\Splunk"

    def install(self, pkg_path, splunk_home=None, **kwargs):
        if splunk_home:
            self.splunk_home = splunk_home

        install_flags = []
        for key, value in kwargs.iteritems():
            install_flags.append('{k}="{v}"'.format(k=key, v=value))

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {f} {q} ' \
              '/L*V "C:\\msi_install.log"'. \
            format(c=pkg_path, h=self.splunk_home, q='/quiet',
                   f=' '.join(install_flags))

        self.pkg_path = pkg_path

        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        if "splunk" == self.splunk_type:
            result = __salt__['service.available']('Splunkd')
        elif "splunkforwarder" == self.splunk_type:
            result = __salt__['service.available']('SplunkForwarder')
        elif self.splunk_type is None:
            result = False
        else:
            raise Exception, "Unexpected splunk_type: {s}".format(
                s=self.splunk_type)

        log.debug('service.available return : %s' % result)
        return result

    def uninstall(self):
        if not is_installed():
            return

        pkg_path = self.pkg_path
        if not pkg_path:
            raise EnvironmentError("Can't uninstall without pkg file")

        cmd = 'msiexec /x {c} /quiet SUPPRESS_SURVEY=1'.format(c=pkg_path)
        result = __salt__['cmd.run_all'](cmd, python_shell=True)
        if result['retcode'] == 0:
            os.remove(pkg_path)
            __salt__['grains.delval']('pkg_path')
            __salt__['grains.delval']('splunk_type')


class LinuxTgzInstaller(Installer):
    def __init__(self, splunk_type):
        super(LinuxTgzInstaller, self).__init__(splunk_type)
        if not self.splunk_home:
            self.splunk_home = "/opt/splunk"

    def install(self, pkg_path, splunk_home=None, **kwargs):
        if splunk_home:
            self.splunk_home = splunk_home

        if self.is_installed():
            cmd = "{s}/bin/splunk stop".format(s=self.splunk_home)
            __salt__['cmd.run_all'](cmd)

        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)

        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license --answer-yes"
               .format(s=self.splunk_home, p=pkg_path))
        self.pkg_path = pkg_path

        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        return os.path.exists(os.path.join(self.splunk_home, "bin", "splunk"))

    def uninstall(self):
        if not self.is_installed():
            return
        cli("stop -f")
        ret = __salt__['cmd.run_all'](
            "rm -rf {h}".format(h=self.splunk_home))
        if 0 == ret['retcode']:
            os.remove(self.pkg_path)
            __salt__['grains.delval']('pkg_path')
            __salt__['grains.delval']('splunk_type')
        else:
            raise CommandExecutionError(ret['stdout'] + ret['stderr'])

        if __salt__['grains.has_value']('splunk_mgmt_uri'):
            __salt__['grains.delval']('splunk_mgmt_uri')


def _is_it_version_branch_build(parameter):
    branch = ''
    version = ''
    build = ''

    result = re.match(r'(^[0-9]{6}$)', parameter)
    if result:
        log.debug('parameter is build number')
        build = parameter
        return branch, version, build

    result = re.match(r'(^[0-9a-z]{12}$)', parameter)
    if result:
        log.debug('parameter is git commit')
        build = parameter
        return branch, version, build

    # todo, find out how to detect pkg is released
    pkg_released = False

    result = re.match(r'(^[0-9]*.[0-9]*.[0-9]*$)', parameter)
    if result:
        log.debug('parameter is version or branch, treat it as branch')
        if pkg_released:
            version = parameter
        else:
            branch = parameter
        return branch, version, build

    log.debug('parameter is branch')
    branch = parameter
    return branch, version, build


def _get_pkg_url(version, branch, build, type='splunk',
                 fetcher_url=FETCHER_URL):
    """
    Get the url for the package to install
    """
    if "linux" in PLATFORM:
        pkg = "Linux-x86_64.tgz"
    elif "win" in PLATFORM:
        pkg = "x64-release.msi"
    else:
        # to do: throw error when platform is not supported
        pkg = "x64-release.msi"

    params = {'PLAT_PKG': pkg, 'DELIVER_AS': 'url'}
    if type == 'splunkforwarder':
        params.update({'UF': '1'})

    params.update({'BRANCH': branch})

    if build:
        params.update({'P4CHANGE': build})
        return _fetch_url(fetcher_url, params)

    if version:
        params.update({'VERSION': version})
        return _fetch_url(fetcher_url, params)

    return _fetch_url(fetcher_url, params)


def _fetch_url(fetcher_url, params):
    r = requests.get(fetcher_url, params=params)
    if 'Error' in r.text.strip():
        raise CommandExecutionError(
            "Fetcher returned an error: {e}, "
            "requested url: {u}".format(
                e=r.text.strip(), u=r.url))
    pkg_url = r.text.strip()
    return pkg_url


def is_installed():
    '''
    check if splunk is installed or not

    :return: True if splunk is installed, else False
    :rtype: Boolean
    '''
    installer = InstallerFactory.create_installer()
    return installer.is_installed()


def install(fetcher_arg,
            type='splunk',
            fetcher_url=FETCHER_URL,
            start_after_install=True,
            is_upgrade=False,
            splunk_home=None,
            **kwargs):
    """
    install Splunk

    :param fetcher_arg: arguments which you want to pass the release fetcher
    :type fetcher_arg: string
    :param type: splunk, splunkforwarder or splunklite
    :type type: string
    :param fetcher_url: url of the release fetcher
    :type fetcher_url: string
    :param start_after_install: True if you want to start splunk right after installation
    :type start_after_install: boolean
    :param is_upgrade: True if you want to upgrade splunk
    :type is_upgrade: bool
    :param splunk_home: path for splunk install to
    :type splunk_home: string
    :rtype: dict
    :return: command line result in dict ['retcode', 'stdout', 'stderr']
    """
    installer = InstallerFactory.create_installer(splunk_type=type)

    if installer.is_installed() and not is_upgrade:
        log.debug('splunk is installed')
        return dict({'retcode': 9,
                     'stdout': 'splunk is installed',
                     'stderr': 'splunk is installed'})

    if fetcher_arg.startswith("http") or fetcher_arg.startswith('salt://'):
        url = fetcher_arg
    else:
        branch, version, build = _is_it_version_branch_build(fetcher_arg)
        url = _get_pkg_url(
            branch=branch, version=version, build=build, type=type,
            fetcher_url=fetcher_url)

    log.debug('download pkg from: {u}'.format(u=url))

    # download the package
    dest_root = tempfile.gettempdir()
    pkg_path = os.path.join(dest_root, os.sep, os.path.basename(url))
    log.debug('download pkg to: {p}'.format(p=pkg_path))

    __salt__['cp.get_url'](path=url, dest=pkg_path)

    return installer.install(pkg_path, splunk_home, **kwargs)


def config_conf(conf_name, stanza_name, data=None, do_restart=True,
                app=None, owner=None, sharing='system'):
    """
    config conf file by REST, if a data is existed, it will skip

    :param conf_name: name of config file
    :param stanza_name: stanza need to config
    :param data: data under stanza
    :param do_restart: restart after configuration
    :param app: namespace of the conf
    :param owner: namespace of the conf
    :param sharing: The scope you want the conf to be. it can be user, app, or system.
    :return: no return value
    :raise EnvironmentError: if restart fail
    """

    splunk = _get_splunk(sharing=sharing, app=app, owner=owner)
    conf = splunk.confs[conf_name]

    if not data:
        data = dict()

    # since data from salt kwargs potentially will come with __pub_* data
    # filter them off here
    data = {key: data[key] for key in data.keys()
            if not key.startswith('__pub_')}

    # lazy load here since splunk sdk is install at run time
    from splunklib.binding import HTTPError
    try:
        try:
            stanza = conf[stanza_name]
        except KeyError:
            log.debug('possible stanza not configured')
            conf.create(stanza_name)
            stanza = conf[stanza_name]

        if data:
            stanza.submit(data)

    except HTTPError as err:
        log.critical('%s is existed' % str(stanza_name))
        log.debug(err)

    if do_restart:
        result = cli('restart')
        log.debug('splunk restart result: %s'
                  % result['stdout'] + result['stderr'])

        if result['retcode'] != 0:
            restart_fail_msg = 'restart fail after config'
            log.critical(restart_fail_msg)
            raise EnvironmentError(restart_fail_msg)


def read_conf(conf_name, stanza_name, key_name=None, owner=None, app=None,
              sharing='system'):
    """
    read config file

    :param conf_name: name of config file
    :param stanza_name: stanza need to config
    :param key_name: key for the value you want to read
    :param owner: namespace of the conf
    :param app: namespace of the conf
    :param sharing: The scope you want the conf to be. it can be user, app, or
        system.
    :return: if no key_name, stanza content will be returned, else will be value
        of given stanza and key_name
    """
    splunk = _get_splunk(sharing=sharing, owner=owner, app=app)

    try:
        conf = splunk.confs[conf_name]
    except KeyError:
        log.warn("no such conf file %s" % conf_name)
        return None

    try:
        stanza = conf[stanza_name]
    except KeyError:
        log.warn('no such stanza, %s' % stanza_name)
        return None

    if not key_name:
        return stanza.content

    if key_name not in stanza.content:
        log.warn('no such key name, %s' % key_name)
        return None

    return stanza[key_name]


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
    :param sharing: The scope you want the conf to be. it can be user, app, or system.
    :return: boolean
    '''
    splunk = _get_splunk(sharing=sharing, owner=owner, app=app)

    try:
        conf = splunk.confs[conf_name]
    except KeyError:
        log.warn("no such conf file %s" % conf_name)
        return None
    return stanza_name in conf


def config_cluster_master(pass4SymmKey, cluster_label, replication_factor=2,
                          search_factor=2):
    """
    config splunk as a master of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethemaster

    :param pass4SymmKey: it's a key to communicate between indexer cluster
    :param cluster_label: the label for indexer cluster
    :param search_factor: factor of bucket be able to search
    :param replication_factor: factor of bucket be able to replicate
    """

    data = {'pass4SymmKey': pass4SymmKey,
            'replication_factor': replication_factor,
            'search_factor': search_factor,
            'mode': 'master',
            'cluster_label': cluster_label,
            }

    config_conf('server', 'clustering', data)


def config_cluster_slave(pass4SymmKey, cluster_label, master_uri=None,
                         replication_port=9887):
    """
    config splunk as a peer(indexer) of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethepeers

    :param pass4SymmKey: is a key to communicate between indexer cluster
    :param cluster_label: the label for indexer cluster
    :param replication_port: port to replicate data
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        indexer-cluster-master
    """
    _random_sleep()

    config_conf('server', "replication_port://{p}".format(p=replication_port),
                do_restart=False)

    if not master_uri:
        master_uri = get_list_of_mgmt_uri('indexer-cluster-master')[0]

    data = {'pass4SymmKey': pass4SymmKey,
            'master_uri': 'https://{u}'.format(u=master_uri),
            'mode': 'slave',
            'cluster_label': cluster_label,
            }

    config_conf('server', 'clustering', data)


def config_cluster_searchhead(pass4SymmKey, cluster_label, master_uri=None):
    """
    config splunk as a search head of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail

    :param pass4SymmKey:  is a key to communicate between indexer cluster
    :param cluster_label: the label for indexer cluster
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        splunk-cluster-master
    """
    _random_sleep()

    if not master_uri:
        master_uri = get_list_of_mgmt_uri('indexer-cluster-master')[0]

    data = {'pass4SymmKey': pass4SymmKey,
            'master_uri': 'https://{u}'.format(u=master_uri),
            'mode': 'searchhead',
            'cluster_label': cluster_label,
            }

    config_conf('server', 'clustering', data)


def config_shcluster_deployer(pass4SymmKey, shcluster_label):
    '''
    config a splunk as a deployer of a search head cluster
    refer to http://docs.splunk.com/Documentation/Splunk/6.3.3/DistSearch/PropagateSHCconfigurationchanges#Choose_an_instance_to_be_the_deployer

    :param shcluster_label: refer to http://docs.splunk.com/Documentation/Splunk/6.3.3/DMC/Setclusterlabels
    :param pass4SymmKey: is a key to communicate between cluster
    '''
    data = {'pass4SymmKey': pass4SymmKey,
            'shcluster_label': shcluster_label}

    config_conf('server', 'shclustering', data=data)


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

    if not conf_deploy_fetch_url:
        conf_deploy_fetch_url = \
            get_list_of_mgmt_uri('search-head-cluster-deployer')[0]

    if not conf_deploy_fetch_url.startswith("https://"):
        conf_deploy_fetch_url = 'https://{u}'.format(u=conf_deploy_fetch_url)

    replication_factor_str = ''
    if replication_factor:
        replication_factor_str = '-replication_factor {n}'.format(
            n=replication_factor)

    cmd = 'init shcluster-config -auth {username}:{password} ' \
          '-mgmt_uri {mgmt_uri} -replication_port {replication_port} ' \
          '{replication_factor_str} ' \
          '-conf_deploy_fetch_url {conf_deploy_fetch_url} ' \
          '-secret {security_key} -shcluster_label {label}' \
        .format(username='admin', password='changeme',
                mgmt_uri='https://{u}'.format(u=get_mgmt_uri()),
                replication_port=replication_port,
                replication_factor_str=replication_factor_str,
                conf_deploy_fetch_url=conf_deploy_fetch_url,
                security_key=pass4SymmKey,
                label=shcluster_label
                )
    result = cli(cmd)
    if result['retcode'] != 0:
        raise CommandExecutionError(result['stderr'] + result['stdout'])

    result = cli('restart')
    if result['retcode'] != 0:
        raise CommandExecutionError(result['stderr'] + result['stdout'])


def bootstrap_shcluster_captain(servers_list=None):
    '''
    bootstrap a splunk instance as a captain of a search head cluster captain

    :param servers_list: list of shc members,
        ex. https://192.168.0.2:8089,https://192.168.0.3:8089
    '''

    if not servers_list:
        servers_list = get_list_of_mgmt_uri('search-head-cluster-member')
        servers_list = ['https://{u}'.format(u=e) for e in servers_list]
        servers_list = ','.join(servers_list)

    cmd = ('bootstrap shcluster-captain -servers_list'
           ' {s} -auth admin:changeme'.format(s=servers_list))

    result = cli(cmd)

    if result['retcode'] != 0:
        return result

    # remove role after bootstrap
    if 'search-head-cluster-first-captain' in __salt__['grains.get']('role'):
        __salt__['grains.remove']('role', 'search-head-cluster-first-captain')

    return result


def remove_search_peer(servers):
    '''
    remove search peer from a search head
    :type servers: list
    :param servers: ex, ['<ip>:<port>','<ip>:<port>', ...]
    '''
    # try to remove servers not in list
    # todo fix username and password
    for s in servers:
        result = cli('remove search-server -auth admin:changeme -url {h}'
                     .format(h=s))
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])


def config_search_peer(
        servers=None, remote_username='admin', remote_password='changeme'):
    '''
    config splunk as a peer of a distributed search environment
    http://docs.splunk.com/Documentation/Splunk/latest/DistSearch/Configuredistributedsearch#Edit_distsearch.conf

    if a search head is part of indexer cluster search head,
    will raise EnvironmentError
    refer to http://docs.splunk.com/Documentation/Splunk/6.3.3/DistSearch/Connectclustersearchheadstosearchpeers#Search_head_cluster_with_indexer_cluster

    :param servers: list value, ex, ['<ip>:<port>','<ip>:<port>']
    :param remote_username: splunk username of the search peer
    :param remote_password: splunk password of the search peer
    :raise CommandExecutionError, if failed
    '''
    if not servers:
        servers = get_list_of_mgmt_uri('indexer')

    # use cli to config is more simple than config by conf file
    # todo fix username and password
    for s in servers:
        result = cli('add search-server -host {h} -auth admin:changeme '
                     '-remoteUsername {u} -remotePassword {p}'
                     .format(h=s, p=remote_password, u=remote_username))
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])


def config_deployment_client(server=None):
    '''
    config deploymeny client
    refer to http://docs.splunk.com/Documentation/Splunk/latest/Updating/Aboutdeploymentserver#Deployment_server_and_clusters

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

    cmd = 'set deploy-poll {s} -auth admin:changeme'.format(s=server)
    cli_result = cli(cmd)
    if cli_result['retcode'] != 0:
        raise CommandExecutionError(str(cli_result))

    restart_result = cli('restart')
    if restart_result['retcode'] != 0:
        raise CommandExecutionError(str(restart_result))


def allow_remote_login():
    '''
    config allowRemoteLogin under server.conf
    '''
    config_conf('server', 'general', {'allowRemoteLogin': 'always'})


def add_license(license_path):
    '''
    :type license_path: string
    :param license_path: where the license is. It should be start with 'salt://'
    '''
    name = os.path.basename(license_path)
    license = __salt__['cp.get_file'](
        license_path, os.path.join(tempfile.gettempdir(), name))

    if license is not None:
        cli_result = cli(
            "add license {l} -auth admin:changeme".format(l=license))
        if 0 == cli_result['retcode']:
            return cli("restart")
        else:
            return cli_result


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

    conf = splunk.confs['server']
    stanza = conf['license']
    stanza.submit({'master_uri': master_uri})
    return splunk.restart(timeout=300)


def get_mgmt_uri():
    '''
    get mgmt uri of splunk

    :return: The mgmt uri of splunk, return None if Splunk is not started
    :rtype: string
    '''
    # todo auth parameter

    cli_result = cli("show splunkd-port -auth admin:changeme")

    if 0 == cli_result['retcode']:
        port = cli_result['stdout'].replace("Splunkd port: ", "").strip()
        mgmt_uri = __grains__['ipv4'][-1] + ":" + port
        __salt__['grains.set']('splunk_mgmt_uri', mgmt_uri, force=True)
        return mgmt_uri
    else:
        return None


def get_list_of_mgmt_uri(role, raise_exception=False, retry_count=5):
    '''
    :param role: grains role matched
    :type role: str
    :rtype: list
    :return: [<ip>:<port>, <ip>:<port>]
    '''

    minions = None
    while True:
        minions = __salt__['mine.get'](role, 'splunk.get_mgmt_uri', 'grain')

        log.warn('runner returned: ' + str(minions))

        if minions and isinstance(minions, dict):
            ret = []
            for key, value in minions.iteritems():
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
    installer = InstallerFactory.create_installer()
    installer.uninstall()


def add_batch_of_user(username_prefix, user_count, roles):
    '''
    Create a large group of user on splunk, user and password are the same

    :param username_prefix: username_prefix, the username will be in form of
        <prefix><number>
    :param user_count: number of user to be created
    :param roles: role of user add to, could be a list or a single role
    '''
    splunk = _get_splunk()
    if not isinstance(roles, list):
        roles = [roles]

    for u in range(user_count):
        user = '{p}{n}'.format(p=username_prefix, n=u)
        splunk.users.create(
            username=user,
            password=user,
            roles=roles
        )


def add_batch_of_saved_search(name_prefix, count, **kwargs):
    '''
    Create a batch of saved search/report/alert
    http://docs.splunk.com/Documentation/Splunk/latest/admin/Savedsearchesconf

    :param name_prefix: prefix name of saved search
    :param count: number of search is going to create
    :param kwargs: any data under a saved search stanza, ex. search="*"
    :return: None
    '''

    for s in range(count):
        search_name = '{p}{c}'.format(p=name_prefix, c=s)
        # restart at the final one
        is_restart = True if s == count - 1 else False
        config_conf('savedsearches', search_name, kwargs, do_restart=is_restart)


def enable_listen(port):
    '''
    enable listening on the splunk instance
    :param port: the port number to enable listening
    :type port: integer
    :return: None
    '''
    result = cli("enable listen {p} -auth admin:changeme".format(p=port))

    if result['retcode'] != 0:
        raise CommandExecutionError(result['stderr'] + result['stdout'])
    else:
        # save the port to grains
        __salt__['grains.append']("listening_ports", port)


def add_forward_server(server):
    '''
    add forward server to the splunk instance
    :param server: server to add to the splunk instance
    :type server: string
    :return: None
    '''
    result = cli("add forward-server {s} -auth admin:changeme".format(s=server))

    if result['retcode'] != 0:
        raise CommandExecutionError(result['stderr'] + result['stdout'])


def add_deployment_app(name):
    '''
    '''
    installer = InstallerFactory.create_installer()
    splunk_home = installer.splunk_home
    cmd = 'mkdir {p}'.format(
        p=os.path.join(splunk_home, 'etc', 'deployment-apps', name))
    return __salt__['cmd.run_all'](cmd)


def add_batch_of_deployment_apps(name_prefix, count):
    '''
    '''
    for i in range(count):
        add_deployment_app(name_prefix + str(i))


def _config_dmc_group(group_name, servers, role_name=None):
    '''
    '''
    if role_name is not None and role_name in __grains__['role']:
        config_conf(
            'distsearch', group_name, {'servers': 'localhost:localhost'},
            do_restart=False)
    else:
        config_conf(
            'distsearch', group_name, {'servers': ','.join(servers)},
            do_restart=False)


def config_dmc():
    '''
    config deployment management console by editing distsearch.conf
    https://confluence.splunk.com/display/PROD/How+to+set+up+DMC+in+Dash

    In the doc, it is assumed that indexer cluster is used, dmc is built on
    indexer cluster master. Therefore we assume that for now, too.
    TODO: update where the dmc should be built by the deployment
    '''
    # add all searchheads and license master as search peer
    searchheads = get_list_of_mgmt_uri('search-head')
    license_master = get_list_of_mgmt_uri('central-license-master')
    deployer = get_list_of_mgmt_uri('search-head-cluster-deployer')
    indexers = get_list_of_mgmt_uri('indexer')

    if 'indexer-cluster-master' in __grains__['role']:
        config_search_peer(searchheads + license_master + deployer)
    else:
        config_search_peer(searchheads + license_master + deployer + indexers)

    # set distsearch groups by editing distsearch.conf
    # indexer
    config_conf('distsearch', 'distributedSearch:dmc_group_indexer',
                {'servers': ','.join(indexers), 'default': True},
                do_restart=False)

    # search head
    config_conf('distsearch', 'distributedSearch:dmc_group_search_head',
                {'servers': ','.join(searchheads)}, do_restart=False)

    # kv store
    config_conf('distsearch', 'distributedSearch:dmc_group_kv_store',
                {'servers': ','.join(searchheads)}, do_restart=False)

    # license master
    _config_dmc_group(
        'distributedSearch:dmc_group_license_master', license_master,
        'central-license-master')

    # cluster_master
    cluster_master = get_list_of_mgmt_uri('indexer-cluster-master')
    _config_dmc_group(
        'distributedSearch:dmc_group_cluster_master', cluster_master,
        'indexer-cluster-master')

    # deployment server
    deployment_server = get_list_of_mgmt_uri('deployment-server')
    _config_dmc_group(
        'distributedSearch:dmc_group_deployment_server', deployment_server,
        'deployment-server')

    # shc deployer
    _config_dmc_group(
        'distributedSearch:dmc_group_shc_deployer', deployer,
        'search-head-cluster-deployer')

    # we should do following steps only after ember
    # todo: add checking version to decide doing them or not

    # config indexer cluster group
    if len(cluster_master) > 0:
        stanza = 'distributedSearch:dmc_indexerclustergroup_{l}'.format(
            l=__pillar__['indexer_cluster']['cluster_label'])

        config_conf(
            'distsearch', stanza, {"servers": ",".join(indexers + searchheads)},
            do_restart=False)

    # config shcluster group if shcluster is enabled
    if len(deployer) > 0:
        stanza = 'distributedSearch:dmc_searchheadclustergroup_{l}'.format(
            l=__pillar__['search_head_cluster']['shcluster_label'])

        config_conf(
            'distsearch', stanza, {"servers": ",".join(searchheads + deployer)},
            do_restart=False)

    # set is_configured flag in splunk_management_console app
    config_conf('app', 'install', {'is_configured': True}, owner="admin",
                app="splunk_management_console", sharing="app",
                do_restart=False)

    # add all machines to splunk_management_console_assets.conf
    all_peers = indexers + searchheads + deployer + deployment_server + \
                license_master
    config_conf('splunk_management_console_assets', 'settings',
                {'configuredPeers': ','.join(all_peers)}, owner="admin",
                app="splunk_management_console", sharing="app", do_restart=True)

    # Run the "DMC Asset - Build Full" saved search
    path = ('https://localhost:8089/servicesNS/nobody/splunk_management_console'
            '/saved/searches/DMC%20Asset%20-%20Build%20Full/dispatch')
    response = requests.post(path, auth=("admin", "changeme"),
                             data={'trigger_actions': 1}, verify=False)


def get_crash_log():
    installer = InstallerFactory.create_installer()
    splunk_home = installer.splunk_home
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
    configured = read_conf('app', 'install', 'is_configured', owner="admin",
                           app="splunk_management_console", sharing="app")
    if "0" == configured or configured is None:
        return False
    else:
        return True


def enable_js_debug_mode():
    '''
    by disabling js cache and minify js, javascript could be debugged by browser console
    '''
    config_conf('server', 'settings', {'js_no_cache': True, 'minify_js': False})
