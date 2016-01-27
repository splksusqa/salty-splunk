import requests
import os
import salt
import tempfile
import sys
import logging
import re
from distutils import util

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


def _get_splunk_home():
    try:
        splunk_home = __pillar__['splunk_home']
    except KeyError:
        splunk_home = ('/opt/splunk' if 'linux' in PLATFORM
                       else 'C:\\Program Files\\Splunk')
    return splunk_home


def cli(cli):
    '''
    run splunk cli
    '''
    splunk_home = _get_splunk_home()
    cmd = '{p} {c}'.format(p=os.path.join(splunk_home, 'bin', 'splunk'), c=cli)
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
        try:
            self.splunk_home = __pillar__['splunk_home']
        except KeyError:
            self.splunk_home = None

    def install(self, pkg_path, splunk_home=None):
        pass

    def is_installed(self):
        pass

    def uninstall(self):
        pass


class WindowsMsiInstaller(Installer):
    def __init__(self):
        '''
        '''
        super(WindowsMsiInstaller, self).__init__()
        if self.splunk_home is None:
            self.splunk_home = "C:\\Program Files\\Splunk"

    def install(self, pkg_path, splunk_home=None):
        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {q}'.format(
                c=pkg_path, h=self.splunk_home, q='/quiet')
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        result = __salt__['service.available']('Splunkd')
        log.debug('service.available return : %s' % result)
        return result

    def uninstall(self):
        raise NotImplementedError


class LinuxTgzInstaller(Installer):
    def __init__(self):
        '''
        '''
        super(LinuxTgzInstaller, self).__init__()
        if self.splunk_home is None:
            self.splunk_home = "/opt/splunk"

    def install(self, pkg_path, splunk_home=None):
        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)
        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license".format(s=self.splunk_home, p=pkg_path))
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        return os.path.exists(os.path.join(self.splunk_home, "bin", "splunk"))

    def uninstall(self):
        if self.is_installed():
            __salt__['cmd.run_all']("{s} stop".format(
                    s=os.path.join(self.splunk_home, "bin", "splunk")))
            ret = __salt__['cmd.run_all'](
                    "rm -rf {h}".format(h=self.splunk_home))
            return 0 == ret['retcode']
        else:
            return True


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
    '''
    Get the url for the package to install
    '''
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
        raise salt.exceptions.CommandExecutionError(
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
            start_after_install=True):
    '''
    install splunk
    '''
    installer = InstallerFactory.create_installer()
    if fetcher_arg.startswith("http") or fetcher_arg.startswith("salt://"):
        url = fetcher_arg
    else:
        branch, version, build = _is_it_version_branch_build(fetcher_arg)
        url = _get_pkg_url(
                branch=branch, version=version, build=build, type=type,
                fetcher_url=fetcher_url)

    # download the package
    dest_root = tempfile.gettempdir()
    pkg_path = os.path.join(dest_root, os.sep, os.path.basename(url))

    __salt__['cp.get_url'](path=url, dest=pkg_path)

    return installer.install(pkg_path)


def config_conf(conf_name, stanza_name, data=None, is_restart=True,
                namespace='system'):
    '''
    config conf file by REST, if a data is existed, it will skip
    :param namespace:
    :param conf_name: name of config file
    :param stanza_name: stanza need to config
    :param data: data under stanza
    :param is_restart: restart after configuration
    :rtype: bool
    :return: True if success, False if not
    '''
    if is_conf_configured(conf_name, stanza_name, data, namespace):
        log.debug('data is configured')
        return True

    splunk = _get_splunk(namespace=namespace)
    conf = splunk.confs[conf_name]

    # lazy load here since splunk sdk is install at run time
    from splunklib.binding import HTTPError
    try:
        if not data:
            conf.create(stanza_name)
        else:
            stanza = conf[stanza_name]
            stanza.submit(data)
        if is_restart:
            result = splunk.restart(timeout=300)
            log.debug('splunk restart result: %s' % result)
            if 200 == result['status']:
                return True
            else:
                log.debug('restart fail after config')
                return False
        return True
    except HTTPError as err:
        log.critical('%s is existed' % str(stanza_name))
        log.debug(err)
        return False
    except KeyError as err:
        log.critical(err)
        return False


def _convert_rest_value_type(target_type, data):
    log.debug('type of data %s ' % type(data).__name__)
    log.debug('target type is %s ' % target_type.__name__)
    if target_type is bool:
        return util.strtobool(str(data))
    else:
        return target_type(str(data))


def is_conf_configured(conf_name, stanza_name, data=None, namespace='system'):
    '''
    right now the function not working because bool value may return 0 instead of False
    need double check
    :param conf_name:
    :param stanza_name:
    :param data:
    :param namespace:
    :return:
    '''
    splunk = _get_splunk(namespace=namespace)

    if conf_name not in splunk.confs:
        log.debug('%s is not exist' % conf_name)
        return False

    conf = splunk.confs[conf_name]
    if stanza_name not in conf:
        log.debug('%s is not exist' % stanza_name)
        return False

    stanza = conf[stanza_name]

    if not data:
        return True

    for key, value in data.iteritems():
        if key not in stanza.content:
            log.debug('%s is not exist' % key)
            return False

        actual_data = stanza.content[key]
        actual_data = _convert_rest_value_type(type(value), actual_data)
        if actual_data != value:
            log.debug('%s, %s is not matched, '
                      'actual value is %s' % (key, value, actual_data))
            return False

    return True


def config_cluster_master(pass4SymmKey, replication_factor=2, search_factor=2):
    '''
    config splunk as a master of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethemaster
    :param search_factor: factor of bucket be able to search
    :param replication_factor: factor of bucket be able to replicate
    :param pass4SymmKey: it's a key to communicate between indexer cluster
    '''

    data = {'pass4SymmKey': pass4SymmKey,
            'replication_factor': replication_factor,
            'search_factor': search_factor,
            'mode': 'master',
            }

    return config_conf('server', 'clustering', data)


def config_cluster_slave(pass4SymmKey, master_uri=None, replication_port=9887):
    '''
    config splunk as a peer(indexer) of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Configurethepeers
    :param replication_port: port to replicate data
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        splunk-cluster-master
    :param pass4SymmKey: is a key to communicate between indexer cluster
    '''
    config_conf('server', "replication_port://{p}".format(p=replication_port),
                is_restart=False)

    if not master_uri:
        master_uri = get_cluster_master_mgmt_uri()

    data = {'pass4SymmKey': pass4SymmKey,
            'master_uri': 'https://{u}'.format(u=master_uri),
            'mode': 'slave',
            }

    return config_conf('server', 'clustering', data)


def config_cluster_searchhead(pass4SymmKey, master_uri=None):
    '''
    config splunk as a search head of a indexer cluster
    http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail
    :param pass4SymmKey:  is a key to communicate between indexer cluster
    :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
        if not specified, will search minion under same master with role
        splunk-cluster-master
    '''
    if not master_uri:
        master_uri = get_cluster_master_mgmt_uri()

    data = {'pass4SymmKey': pass4SymmKey,
            'master_uri': 'https://{u}'.format(u=master_uri),
            'mode': 'searchhead',
            }

    return config_conf('server', 'clustering', data)


def get_cluster_master_mgmt_uri(target='role:splunk-cluster-master',
                                expr='grain'):
    '''
    get mgmt uri of splunk instance with 'role:splunk-cluster-master'
    :param expr:
    :param target:
    :return: uri of 'role:splunk-cluster-master' in <ip>:<port> form
    '''
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

    return config_conf('server', 'shclustering', data=data)


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
    '''
    config splunk as a member of a search head cluster
    :param conf_deploy_fetch_url:
    :param replication_port:
    :param replication_factor:
    :param shcluster_label:
    :param pass4SymmKey:
    '''
    stanza = "replication_port://{p}".format(p=replication_port)
    result = config_conf('server', stanza, is_restart=False)
    if not result:
        return False

    if not conf_deploy_fetch_url:
        conf_deploy_fetch_url = get_deployer_uri()

    if not conf_deploy_fetch_url.startswith("https://"):
        conf_deploy_fetch_url = 'https://{u}'.format(u=conf_deploy_fetch_url)

    data = {'pass4SymmKey': pass4SymmKey,
            'shcluster_label': shcluster_label,
            'conf_deploy_fetch_url': conf_deploy_fetch_url,
            'mgmt_uri': 'https://{u}'.format(u=get_mgmt_uri()),
            'disabled': 'false'}

    return config_conf('server', 'shclustering', data)


def bootstrap_shcluster_captain(servers_list=None):
    '''
    bootstrap a splunk instance as a captain of a search head cluster captain
    :param servers_list: list of shc members,
        ex. https://192.168.0.2:8089,https://192.168.0.3:8089
    '''

    servers_list = servers_list if servers_list else get_shc_member_list()

    cmd = ('bootstrap shcluster-captain -servers_list'
           ' {s} -auth admin:changeme'.format(s=servers_list))
    return cli(cmd)


def get_indexer_list():
    '''
    :rtype: list
    :return: [<ip>:<port>, <ip>:<port>]
    '''
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
    '''
    config splunk as a peer of a distributed search environment
    http://docs.splunk.com/Documentation/Splunk/latest/DistSearch/Configuredistributedsearch#Edit_distsearch.conf
    :param remote_password:
    :param remote_username:
    :param servers: <ip>:<port>,<ip>:<port>
    '''
    if not servers:
        servers = get_indexer_list()

    # use cli to config is more simple than config by conf file

    result_list = []
    for s in servers:
        result = cli('add search-server -host {h} -auth admin:changeme '
                     '-remoteUsername {u} -remotePassword {p}'
                     .format(h=s, p=remote_password, u=remote_username))
        result_list.append(result)

    return result_list


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
    '''
    config deploymeny client
    :param server: mgmt uri of deployment server
    '''
    if not server:
        server = get_deployment_server_mgmt_url()

    cmd = 'set deploy-poll {s} -auth admin:changeme'.format(s=server)
    cli_result = cli(cmd)

    if 0 == cli_result['retcode']:
        return cli('restart')
    else:
        return cli_result


def allow_remote_login():
    '''
    config allowRemoteLogin under server.conf
    '''
    return config_conf('server', 'general', {'allowRemoteLogin': 'always'})


def get_mgmt_uri():
    '''
    '''
    return __grains__['ipv4'][-1] + ":8089"


def uninstall():
    '''
    uninstall splunk
    '''
    installer = InstallerFactory.create_installer()
    return installer.uninstall()


def get_shc_member_list():
    '''
    '''
    ips = __salt__['publish.publish'](
            'role:splunk-shcluster-member', 'splunk.get_mgmt_uri', None,
            'grain')
    return ",".join(["https://{p}".format(p=ip) for ip in ips.values()])
