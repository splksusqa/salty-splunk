import requests
import os
import salt
import tempfile
import sys
import logging
import re

PLATFORM = sys.platform
FETCHER_URL = 'http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'

def _import_sdk():
    try:
        import splunklib
    except ImportError:
        if "win" in PLATFORM:
            __salt__['pip.install'](
                pkgs='splunk-sdk', bin_env='C:\\salt\\bin\\Scripts\\pip.exe',
                cwd="C:\\salt\\bin\\scripts")
        else:
            __salt__['pip.install']('splunk-sdk')
        import splunklib
    return splunklib

def _get_splunk(username="admin", password="changeme"):
    '''
    returns the object which represents a splunk instance
    '''
    splunklib = _import_sdk()
    import splunklib.client as client

    splunk = client.connect(
        username=username, password=password, sharing="system", autologin=True)
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

    def get_pkg_path(self):
        return __salt__['grains.get']('pkg_path')

    def set_pkg_path(self, pkg_path):
        return __salt__['grains.set']('pkg_path', pkg_path, force=True)

class WindowsMsiInstaller(Installer):
    def __init__(self):
        '''
        '''
        super(WindowsMsiInstaller, self).__init__()
        if self.splunk_home is None:
            self.splunk_home = "C:\\Program Files\\Splunk"

    def install(self, pkg_path, splunk_home=None):
        splunk_home = splunk_home if splunk_home else self.splunk_home

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {q}'.format(
            c=pkg_path, h=splunk_home, q='/quiet')
        self.set_pkg_path(pkg_path)
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        result = __salt__['service.available']('Splunkd')
        log.debug('service.available return : %s' % result)
        return result

    def uninstall(self):
        if not is_installed():
            return dict({'retcode': 9,
                         'stdout': '',
                         'stderr': 'is not installed'})

        pkg_path = self.get_pkg_path()
        if not pkg_path:
            raise EnvironmentError("Can't uninstall without pkg file")

        cmd = 'msiexec /x {c} /quiet SUPPRESS_SURVEY=1'.format(c=pkg_path)
        result = __salt__['cmd.run_all'](cmd, python_shell=True)
        if result['retcode'] == 0:
            os.remove(pkg_path)
            __salt__['grains.delval']('pkg_path')

        return result


class LinuxTgzInstaller(Installer):
    def __init__(self):
        '''
        '''
        super(LinuxTgzInstaller, self).__init__()
        if self.splunk_home is None:
            self.splunk_home = "/opt/splunk"

    def install(self, pkg_path, splunk_home=None):
        splunk_home = splunk_home if splunk_home else self.splunk_home

        if self.is_installed():
            cmd = "{s}/bin/splunk stop".format(s=splunk_home)
            __salt__['cmd.run_all'](cmd)

        if not os.path.exists(splunk_home):
            os.mkdir(splunk_home)

        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license --answer-yes"
               .format(s=self.splunk_home, p=pkg_path))
        self.set_pkg_path(pkg_path)
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
            start_after_install=True,
            is_upgrade=False):
    '''
    install splunk
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
    '''
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

    return installer.install(pkg_path)

def config_cluster_master(pass4SymmKey, replication_factor=2, search_factor=2):
    '''
    '''
    splunk = _get_splunk()

    conf = splunk.confs['server']
    stanza = conf['clustering']
    # choose one of update and submit
    stanza.submit({'pass4SymmKey': pass4SymmKey,
                   'replication_factor': replication_factor,
                   'search_factor': search_factor,
                   'mode': 'master',})
    return splunk.restart(timeout=60)

def config_cluster_slave(pass4SymmKey, master_uri, replication_port):
    '''
    '''
    splunk = _get_splunk()

    conf = splunk.confs['server']
    conf.create("replication_port://{p}".format(p=replication_port))
    stanza = conf['clustering']
    # choose one of update and submit
    stanza.submit({'pass4SymmKey': pass4SymmKey,
                   'master_uri': 'https://{u}'.format(u=master_uri),
                   'mode': 'slave',})
    return splunk.restart(timeout=60)

def config_cluster_searchhead(pass4SymmKey, master_uri):
    '''
    '''
    splunk = _get_splunk()

    conf = splunk.confs['server']
    stanza = conf['clustering']
    # choose one of update and submit
    stanza.submit({'pass4SymmKey': pass4SymmKey,
                   'master_uri': 'https://{u}'.format(u=master_uri),
                   'mode': 'searchhead',})
    return splunk.restart(timeout=60)

def config_shcluster_deployer(pass4SymmKey, shcluster_label):
    '''
    config deployer of the shc
    '''
    splunk = _get_splunk()
    conf = splunk.confs['server']
    stanza = conf['shclustering']
    stanza.submit({'pass4SymmKey': pass4SymmKey,
                   'shcluster_label': shcluster_label})
    return splunk.restart(timeout=60)

def config_shcluster_member(
        pass4SymmKey, shcluster_label, replication_factor, replication_port,
        conf_deploy_fetch_url):
    '''
    config shcluster member
    '''
    splunk = _get_splunk()
    if not conf_deploy_fetch_url.startswith("https://"):
        conf_deploy_fetch_url = 'https://{u}'.format(u=conf_deploy_fetch_url)

    from splunklib.binding import HTTPError
    conf = splunk.confs['server']
    try:
        conf.create("replication_port://{p}".format(p=replication_port))
    except HTTPError:
        pass  # the replication_port stanza is already there

    stanza = conf['shclustering']
    stanza.submit({'pass4SymmKey': pass4SymmKey,
                   'shcluster_label': shcluster_label,
                   'conf_deploy_fetch_url': conf_deploy_fetch_url,
                   'mgmt_uri': 'https://{u}'.format(u=get_mgmt_uri()),
                   'disabled': 'false'})
    return splunk.restart(timeout=60)

def bootstrap_shcluster_captain(servers_list):
    '''
    bootstrap shcluster captain
    '''
    # dont like this, let's fix this later

    cmd = ('bootstrap shcluster-captain -servers_list'
           ' {s} -auth admin:changeme'.format(s=servers_list))
    return cli(cmd)

def config_search_peer(
        servers, remote_username='admin', remote_password='changeme'):
    '''
    config search peer
    '''
    return cli('add search-server -host {h} -auth admin:changeme '
               '-remoteUsername {u} -remotePassword {p}'.format(
                h=servers, p=remote_password, u=remote_username))

def config_deployment_client(server):
    '''
    config deploymeny client
    '''
    cmd = 'set deploy-poll {s} -auth admin:changeme'.format(s=server)
    cli_result = cli(cmd)

    if 0 == cli_result['retcode']:
        return cli('restart')
    else:
        return cli_result

def allow_remote_login():
    '''
    '''
    splunk = _get_splunk()
    conf = splunk.confs['server']
    stanza = conf['general']
    stanza.submit({'allowRemoteLogin': 'always'})

    return splunk.restart(timeout=60)

def get_mgmt_uri():
    '''
    '''
    return __grains__['ipv4'][-1] + ":8089"

def uninstall():
    '''
    '''
    installer = InstallerFactory.create_installer()
    return installer.uninstall()

def get_shc_member_list():
    '''
    '''
    ips = __salt__['publish.publish'](
        'role:splunk-shcluster-member', 'splunk.get_mgmt_uri', None, 'grain')
    return ",".join(["https://{p}".format(p=ip) for ip in ips.values()])
