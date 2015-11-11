import requests
import sys
import os
import salt

PLATFORM = sys.platform

def hello(a):
    return a

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

def install(splunk_home,
            version,
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
    platform = sys.platform
    if "linux" in platform:
        dest_root = "/opt"
    elif "win" in platform:
        dest_root = 'C:'
    else:
        # to do: throw error when platform is not supported
        dest_root = "/opt"

    pkg_path = os.path.join(dest_root, os.sep, os.path.basename(url))

    __salt__['cp.get_url'](path=url, dest=pkg_path)

    if not os.path.exists(splunk_home):
        os.mkdir(splunk_home)

    # install the package
    if "linux" in platform:
        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license".format(s=splunk_home, p=pkg_path))
    elif "win" in platform:
        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {q}'.format(
            c=pkg_path, h=splunk_home, q='/quiet')
    else:
        # to do: throw error when platform is not supported
        cmd = "tar --strip-components=1 -xf {p} -C {s}".format(
            s=splunk_home, p=pkg_path)

    __salt__['cmd.run_all'](cmd, python_shell=True)
