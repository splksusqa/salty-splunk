import requests
import os
import salt
import tempfile
import sys
import logging


log = logging.getLogger(__name__)


class InstallerFactory:
    def __init__(self):
        pass

    @staticmethod
    def create_installer():
        platform = sys.platform
        if "linux" in platform:
            installer = LinuxTgzInstaller()
        elif "win" in platform:
            installer = WindowsMsiInstaller()
        else:
            # to do: throw error when platform is not supported
            raise NotImplementedError
        return installer


class Installer:
    def __init__(self):
        pass

    def install(self, pkg_path, splunk_home=None):
        pass

    def is_installed(self):
        pass


class WindowsMsiInstaller(Installer):
    def install(self, pkg_path, splunk_home=None):
        if splunk_home is None:
            splunk_home = "C:\\Program Files\\Splunk"

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {q}'.format(
            c=pkg_path, h=splunk_home, q='/quiet')
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        result = __salt__['service.available']('Splunkd')
        log.debug('service.available return : %s' % result)
        return result


class LinuxTgzInstaller(Installer):
    def install(self, pkg_path, splunk_home=None):
        if splunk_home is None:
            splunk_home = "/opt/splunk"

        if not os.path.exists(splunk_home):
            os.mkdir(splunk_home)
        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license".format(s=splunk_home, p=pkg_path))
        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        raise NotImplementedError


INSTALLER = InstallerFactory.create_installer()


def _get_pkg_url(version, build='', type='splunk', pkg_released=False,
                 fetcher_url='http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'):
    '''
    Get the url for the package to install
    '''
    platform = sys.platform
    if "linux" in platform:
        pkg = "Linux-x86_64.tgz"
    elif "win" in platform:
        pkg = "x64-release.msi"
    else:
        # to do: throw error when platform is not supported
        pkg = "x64-release.msi"

    params = {'PLAT_PKG': pkg, 'DELIVER_AS': 'url'}
    if type == 'splunkforwarder':
        params.update({'UF': '1'})

    if pkg_released:
        params.update({'VERSION': version})
    else:
        params.update({'BRANCH': version})
        if build:
            params.update({'P4CHANGE': build})

    r = requests.get(fetcher_url, params=params)
    if 'Error' in r.text.strip():
        raise salt.exceptions.CommandExecutionError(
            "Fetcher returned an error: {e}, "
            "requested url: {u}".format(
                e=r.text.strip(), u=r.url))
    pkg_url = r.text.strip()
    return pkg_url


def is_installed():
    return INSTALLER.is_installed()


def install(version,
            splunk_home=None,
            build='',
            type='splunk',
            pkg_released=False,
            fetcher_url='http://r.susqa.com/cgi-bin/splunk_build_fetcher.py',
            start_after_install=True):
    '''
    install splunk
    '''
    url = _get_pkg_url(version=version, build=build, type=type,
                       pkg_released=pkg_released, fetcher_url=fetcher_url)

    # download the package
    dest_root = tempfile.gettempdir()
    pkg_path = os.path.join(dest_root, os.sep, os.path.basename(url))

    __salt__['cp.get_url'](path=url, dest=pkg_path)

    return INSTALLER.install(pkg_path)
