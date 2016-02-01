import requests
import os
import tempfile
import sys
import logging
import re
from salt.exceptions import CommandExecutionError

PLATFORM = sys.platform
FETCHER_URL = 'http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'


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


def _get_splunk(username="admin", password="changeme", namespace='system'):
    """
    returns the object which represents a splunk instance
    """
    splunklib = _import_sdk()
    import splunklib.client as client

    splunk = client.connect(
            username=username, password=password, sharing=namespace,
            autologin=True)
    return splunk


def cli(command):
    """
    run splunk cli
    :param command: splunk cli command, ex. 'add listen 9997'
    """
    installer = InstallerFactory.create_installer()
    splunk_home = installer.splunk_home
    cmd = '{p} {c}'.format(p=os.path.join(splunk_home, 'bin', 'splunk'),
                           c=command)
    return __salt__['cmd.run_all'](cmd)


log = logging.getLogger(__name__)


class InstallerFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def create_installer():
        if "linux" in PLATFORM:
            installer = LinuxTgzInstaller()
        elif "win" in PLATFORM:
            installer = WindowsMsiInstaller()
        else:
            # to do: throw error when platform is not supported
            raise NotImplementedError
        return installer


class Installer(object):
    def __init__(self):
        pass

    def install(self, pkg_path, splunk_home=None):
        pass

    def is_installed(self):
        pass

    def uninstall(self):
        pass

    @property
    def pkg_path(self):
        """ where the package file is stored"""
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


class WindowsMsiInstaller(Installer):
    def __init__(self):
        super(WindowsMsiInstaller, self).__init__()
        if not self.splunk_home:
            self.splunk_home = "C:\\Program Files\\Splunk"

    def install(self, pkg_path, splunk_home=None):
        if splunk_home:
            self.splunk_home = splunk_home

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {q}'.format(
                c=pkg_path, h=self.splunk_home, q='/quiet')
        self.pkg_path = pkg_path

        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        result = __salt__['service.available']('Splunkd')
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


class LinuxTgzInstaller(Installer):
    def __init__(self):
        super(LinuxTgzInstaller, self).__init__()
        if not self.splunk_home:
            self.splunk_home = "/opt/splunk"

    def install(self, pkg_path, splunk_home=None):
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

        __salt__['cmd.run_all']("{s} stop".format(
                s=os.path.join(self.splunk_home, "bin", "splunk")))
        ret = __salt__['cmd.run_all'](
                "rm -rf {h}".format(h=self.splunk_home))
        if 0 == ret['retcode']:
            os.remove(self.pkg_path)
            __salt__['grains.delval']('pkg_path')
        else:
            raise CommandExecutionError(ret['stdout'] + ret['stderr'])


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
    installer = InstallerFactory.create_installer()
    return installer.is_installed()


def install(fetcher_arg,
            type='splunk',
            fetcher_url=FETCHER_URL,
            start_after_install=True,
            is_upgrade=False,
            splunk_home=None):
    """
    install Splunk
    :type fetcher_arg: str
    :type type: str
    :type fetcher_url: str
    :type start_after_install: bool
    :type is_upgrade: bool
    :rtype dict
    :return command line result in dict ['retcode', 'stdout', 'stderr']
    :param is_upgrade: bool, if splunk exists, upgrade splunk
    :param start_after_install:
    :param fetcher_url: string, where you download splunk pkg from
    :param type: string, product type, ['splunk', 'uf', 'cloud' or 'light']
    :param fetcher_arg: string, [version, hash, build_no, url or salt://url]
    """
    installer = InstallerFactory.create_installer()

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

    return installer.install(pkg_path, splunk_home)


def config_conf(conf_name, stanza_name, data=None, do_restart=True,
                namespace='system'):
    """
    config conf file by REST, if a data is existed, it will skip
    :param namespace:
    :param conf_name: name of config file
    :param stanza_name: stanza need to config
    :param data: data under stanza
    :param do_restart: restart after configuration
    :return: no return value
    :raise EnvironmentError: if restart fail
    """

    splunk = _get_splunk(namespace=namespace)
    conf = splunk.confs[conf_name]

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
        result = splunk.restart(timeout=300)
        log.debug('splunk restart result: %s' % result)
        if 200 == result['status']:
            return
        else:
            restart_fail_msg = 'restart fail after config'
            log.critical(restart_fail_msg)
            raise EnvironmentError(restart_fail_msg)


def config_cluster_master(pass4SymmKey, replication_factor=2, search_factor=2):
    """
    config splunk as a master of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethemaster
    :param search_factor: factor of bucket be able to search
    :param replication_factor: factor of bucket be able to replicate
    :param pass4SymmKey: it's a key to communicate between indexer cluster
    """

    data = {'pass4SymmKey': pass4SymmKey,
            'replication_factor': replication_factor,
            'search_factor': search_factor,
            'mode': 'master',
            }

    config_conf('server', 'clustering', data)


def config_cluster_slave(pass4SymmKey, master_uri=None, replication_port=9887):
    """
    config splunk as a peer(indexer) of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethepeers
    :param replication_port: port to replicate data
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        splunk-cluster-master
    :param pass4SymmKey: is a key to communicate between indexer cluster
    """
    config_conf('server', "replication_port://{p}".format(p=replication_port),
                do_restart=False)

    if not master_uri:
        master_uri = get_cluster_master_mgmt_uri()

    data = {'pass4SymmKey': pass4SymmKey,
            'master_uri': 'https://{u}'.format(u=master_uri),
            'mode': 'slave',
            }

    config_conf('server', 'clustering', data)


def config_cluster_searchhead(pass4SymmKey, master_uri=None):
    """
    config splunk as a search head of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail
    :param pass4SymmKey:  is a key to communicate between indexer cluster
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        splunk-cluster-master
    """
    if not master_uri:
        master_uri = get_cluster_master_mgmt_uri()

    data = {'pass4SymmKey': pass4SymmKey,
            'master_uri': 'https://{u}'.format(u=master_uri),
            'mode': 'searchhead',
            }

    config_conf('server', 'clustering', data)


def get_cluster_master_mgmt_uri(target='role:splunk-cluster-master',
                                expr='grain'):
    """
    get mgmt uri of splunk instance with 'role:splunk-cluster-master'
    :param expr:
    :param target:
    :return: uri of 'role:splunk-cluster-master' in <ip>:<port> form
    """
    func_name = 'splunk.get_mgmt_uri'

    # return type is dict
    minions = __salt__['publish.publish'](target, func_name, expr_form=expr)

    if not minions or len(minions.values()) != 1:
        raise EnvironmentError(
                "should be one %s under master, count %d" %
                (target, len(minions.values())))

    uri = minions.values()[0]
    return uri


def config_shcluster_deployer(pass4SymmKey, shcluster_label):
    '''
    config splunk as a deployer of the search head cluster
    :return result of splunk restart
    '''
    data = {'pass4SymmKey': pass4SymmKey,
            'shcluster_label': shcluster_label}

    config_conf('server', 'shclustering', data=data)


def get_deployer_uri():
    target = 'role:splunk-shcluster-deployer'
    func_name = 'splunk.get_mgmt_uri'
    exp = 'grain'
    minions = __salt__['publish.publish'](target, func_name, expr_form=exp)

    if not minions or len(minions.values()) != 1:
        raise EnvironmentError(
                "should be one %s under master, count %d" %
                (target, len(minions.values())))

    uri = minions.values()[0]

    return uri


def config_shcluster_member(
        pass4SymmKey, shcluster_label, replication_factor, replication_port,
        conf_deploy_fetch_url=None):
    """
    config splunk as a member of a search head cluster
    :param conf_deploy_fetch_url:
    :param replication_port:
    :param replication_factor:
    :param shcluster_label:
    :param pass4SymmKey:
    """
    stanza = "replication_port://{p}".format(p=replication_port)
    config_conf('server', stanza, do_restart=False)

    if not conf_deploy_fetch_url:
        conf_deploy_fetch_url = get_deployer_uri()

    if not conf_deploy_fetch_url.startswith("https://"):
        conf_deploy_fetch_url = 'https://{u}'.format(u=conf_deploy_fetch_url)

    data = {'pass4SymmKey': pass4SymmKey,
            'shcluster_label': shcluster_label,
            'conf_deploy_fetch_url': conf_deploy_fetch_url,
            'mgmt_uri': 'https://{u}'.format(u=get_mgmt_uri()),
            'disabled': 'false'}

    config_conf('server', 'shclustering', data)


def bootstrap_shcluster_captain(servers_list=None):
    """
    bootstrap a splunk instance as a captain of a search head cluster captain
    :param servers_list: list of shc members,
        ex. https://192.168.0.2:8089,https://192.168.0.3:8089
    """

    servers_list = servers_list if servers_list else get_shc_member_list()

    cmd = ('bootstrap shcluster-captain -servers_list'
           ' {s} -auth admin:changeme'.format(s=servers_list))
    return cli(cmd)


def get_indexer_list():
    """
    :rtype: list
    :return: [<ip>:<port>, <ip>:<port>]
    """
    target = 'role:splunk-shcluster-indexer'
    func_name = 'splunk.get_mgmt_uri'
    exp = 'grain'
    minions = __salt__['publish.publish'](target, func_name, expr_form=exp)

    if not minions:
        raise EnvironmentError(
                "should be at least %s under master, count %d" %
                (target, len(minions.values())))

    return minions.values()


def config_search_peer(
        servers=None, remote_username='admin', remote_password='changeme'):
    """
    config splunk as a peer of a distributed search environment
    http://docs.splunk.com/Documentation/Splunk/latest/DistSearch/Configuredistributedsearch#Edit_distsearch.conf
    :param remote_password:
    :param remote_username:
    :param servers: <ip>:<port>,<ip>:<port>
    """
    if not servers:
        servers = get_indexer_list()

    # use cli to config is more simple than config by conf file
    for s in servers:
        result = cli('add search-server -host {h} -auth admin:changeme '
                     '-remoteUsername {u} -remotePassword {p}'
                     .format(h=s, p=remote_password, u=remote_username))
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])


def get_deployment_server_mgmt_url():
    target = 'role:splunk-deployment-server'
    func_name = 'splunk.get_mgmt_uri'
    expr = 'grain'

    # return type is dict
    minions = __salt__['publish.publish'](target, func_name, expr_form=expr)

    if not minions or len(minions.values()) != 1:
        raise EnvironmentError(
                "should be one %s under master, count %d" %
                (target, len(minions.values())))

    uri = minions.values()[0]
    return uri


def config_deployment_client(server=None):
    """
    config deploymeny client
    :param server: mgmt uri of deployment server
    """
    if not server:
        server = get_deployment_server_mgmt_url()

    cmd = 'set deploy-poll {s} -auth admin:changeme'.format(s=server)
    cli_result = cli(cmd)
    if cli_result['retcode'] != 0:
        raise CommandExecutionError(str(cli_result))

    restart_result = cli('restart')
    if restart_result['retcode'] != 0:
        raise CommandExecutionError(str(restart_result))


def allow_remote_login():
    """
    config allowRemoteLogin under server.conf
    """
    config_conf('server', 'general', {'allowRemoteLogin': 'always'})


def add_license(license_path):
    '''
    @type license_path: string
    @param license_path: where the license is. It should be start with 'salt://'
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


def config_license_slave(master_uri):
    '''
    '''
    splunk = _get_splunk()
    conf = splunk.confs['server']

    if not master_uri.startswith("https://"):
        master_uri = 'https://{u}'.format(u=master_uri)
    stanza = conf['license']
    stanza.submit({'master_uri': master_uri})
    return splunk.restart(timeout=300)


def get_mgmt_uri():
    """
    get mgmt uri of splunk
    """
    cli_result = cli("show splunkd-port -auth admin:changeme")

    if 0 == cli_result['retcode']:
        port = cli_result['stdout'].replace("Splunkd port: ", "")
        return __grains__['ipv4'][-1] + ":" + port
    else:
        raise CommandExecutionError(str(cli_result))



def uninstall():
    """
    uninstall splunk
    """
    installer = InstallerFactory.create_installer()
    installer.uninstall()


def get_shc_member_list():
    """
    :return <ip>:<port>, <ip>:<port>
    """
    ips = __salt__['publish.publish'](
            'role:splunk-shcluster-member', 'splunk.get_mgmt_uri', None,
            'grain')
    return ",".join(["https://{p}".format(p=ip) for ip in ips.values()])


def add_batch_of_user(username_prefix, user_count, roles):
    """
    Create a large group of user on splunk, user and password are the same
    :param username_prefix: username_prefix, the username will be in form of
        <prefix><number>
    :param user_count: number of user to be created
    :param roles: role of user add to, could be a list or a single role
    """
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
    """
    Create a batch of saved search/report/alert
    http://docs.splunk.com/Documentation/Splunk/latest/admin/Savedsearchesconf
    :param name_prefix: prefix name of saved search
    :param count: number of search is going to create
    :param kwargs: any data under a saved search stanza, ex. search="*"
    :return: None
    """

    for s in range(count):
        search_name = '{p}{c}'.format(p=name_prefix, c=s)
        # restart at the final one
        is_restart = True if s == count - 1 else False
        config_conf('savedsearches', search_name, kwargs, do_restart=is_restart)
