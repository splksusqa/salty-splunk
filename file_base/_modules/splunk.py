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
        self.splunk_home = (
            __pillar__['splunk_home'] if __pillar__['splunk_home'] else None)

    def install(self, pkg_path, splunk_home=None):
        pass

    def is_installed(self):
        pass


class WindowsMsiInstaller(Installer):
    def install(self, pkg_path, splunk_home=None):
        if self.splunk_home is None:
            self.splunk_home = "C:\\Program Files\\Splunk"

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {q}'.format(
            c=pkg_path, h=self.splunk_home, q='/quiet')
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        result = __salt__['service.available']('Splunkd')
        log.debug('service.available return : %s' % result)
        return result


class LinuxTgzInstaller(Installer):
    def install(self, pkg_path, splunk_home=None):
        if self.splunk_home is None:
            self.splunk_home = "/opt/splunk"

        if not os.path.exists(splunk_home):
            os.mkdir(splunk_home)
        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license".format(s=self.splunk_home, p=pkg_path))
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        return os.path.exists(os.path.join(self.splunk_home, "bin", "splunk"))


# INSTALLER = InstallerFactory.create_installer()


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
    branch, version, build = _is_it_version_branch_build(fetcher_arg)
    url = _get_pkg_url(
        branch=branch, version=version, build=build, type=type,
        fetcher_url=fetcher_url)

    # download the package
    dest_root = tempfile.gettempdir()
    pkg_path = os.path.join(dest_root, os.sep, os.path.basename(url))

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
