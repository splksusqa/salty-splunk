import salt
import logging
import platform
import re
from datetime import datetime
import shutil
import time
import socket
import urllib2
import os
import logging
import hashlib

logger = logging.getLogger(__name__)
HOSTS = [{"name": "TW", "url": "http://172.18.90.221"},
         {"name": "SF", "url": 'http://10.160.23.144'}]


class Downloader():
    def __init__(self):
        pass

    #
    # ['product','version','buildnum','']

    class PackagePlatformFactory():
        def __init__(self):
            pass

        @staticmethod
        def create(target_platform, target_arch):
            """
            get the package name by system's platform
            """
            if target_platform is None:
                target_platform = platform.system()

            if target_arch is None:
                target_arch = platform.machine()

            if "linux" in target_platform.lower():
                if "64" in target_arch:
                    return "Linux-x86_64.tgz"
                else:
                    raise NotImplementedError
            elif "darwin" in target_platform.lower():
                if "64" in target_arch:
                    return "darwin-64.tgz"
                else:
                    return "Darwin-universal.tgz"
            elif "windows" in target_platform.lower():
                if "64" in target_arch:
                    return "x64-release.msi"
                else:
                    return "x86-release.msi"
            else:
                raise NotImplementedError

    class State:
        def __init__(self, url=""):
            self.url = url

        def next(self, args):
            return NotImplementedError

    class FetchUrlStateMachine:
        def __init__(self):
            self.current_state = Downloader.PlatformArchiveState()
            self.log = logging.getLogger()

        def get_link(self, args):
            args.log = self.log
            while not isinstance(self.current_state, Downloader.ResultState):
                self.current_state = self.current_state.next(args)
            return self.current_state.url

    class ResultState(State):
        pass

    class PlatformArchiveState(State):
        def next(self, args):
            url = self.url
            args.platform = Downloader.PackagePlatformFactory.create(
                target_platform=args.platform,
                target_arch=args.architecture)
            url += "&PLAT_PKG=" + args.platform
            return Downloader.CheckLocalRepositoryState(url)

    # todo how to check local without network connection?
    class CheckLocalRepositoryState(State):
        # todo , only p4 change could be find now
        @staticmethod
        def _find_local_package(p4change, target_platform, local_repository):
            if not os.path.exists(local_repository):
                return None

            if p4change is None:
                return None

            for path in os.listdir(local_repository):
                match_obj = re.match(
                    r'splunk-.*-%s-%s' % (p4change, target_platform), path,
                    re.M | re.I)
                if match_obj:
                    return match_obj.group()
            return None

        def next(self, args):
            local_file_path = self._find_local_package(args.p4change,
                                                       args.platform,
                                                       args.localRepository)
            if local_file_path:
                self.url = local_file_path
                return Downloader.ResultState(self.url)
            return Downloader.BuildNumberState(self.url)

    class BuildNumberState(State):
        def next(self, args):
            if args.p4change and args.p4change != '':
                self.url += "&P4CHANGE=" + args.p4change
                return Downloader.UniversalForwarderState(self.url)
            return Downloader.VersionState(self.url)

    class UniversalForwarderState(State):
        def next(self, args):
            if args.uf is not None and args.uf is True:
                self.url += "&UF=" + "1"
            return Downloader.HostState(self.url)

    class VersionState(State):
        def next(self, args):
            if args.version is None or args.version == '':
                return Downloader.BranchState(self.url)
            self.url += "&VERSION=" + args.version
            return Downloader.UniversalForwarderState(self.url)

    class BranchState(State):
        def next(self, args):
            if args.branch is None or args.branch == '':
                raise ValueError('branch or version number is needed')
            self.url += "&BRANCH=" + args.branch
            return Downloader.UniversalForwarderState(self.url)

    class HostState(State):
        def next(self, args):
            self.url = "/cgi-bin/splunk_build_fetcher.py?DELIVER_AS=url" + self.url
            self.url = self.check_host_and_create_link(self.url, args.log)
            if args.url_only:
                return Downloader.ResultState(self.url)
            return Downloader.DownloadState(self.url)

        @staticmethod
        def get_hosts():
            hosts = HOSTS
            return hosts

        @staticmethod
        def sort_by_host_speed(hosts):
            key_conn_time = "connection_time"
            flag_of_failed_site = -1
            for host in hosts:
                Downloader.HostState.test_speed(
                    flag_of_failed_site, host, key_conn_time)

            hosts = filter(
                lambda x: x[key_conn_time] != flag_of_failed_site, hosts)
            hosts.sort(key=lambda x: x[key_conn_time])
            return hosts

        @staticmethod
        def test_speed(flag_of_failed_site, host, key_name_time):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                time_before = time.time()
                ip = ''
                port = ''
                sock.connect((ip, port))
                host[key_name_time] = time.time() - time_before
            except socket.error:
                host[key_name_time] = flag_of_failed_site
                logger.info(host["name"] + " is down")
            finally:
                sock.close()

        def check_host_and_create_link(self, url, log):
            """
            get the fetcher hostname
            """
            hosts = self.get_hosts()
            hosts = self.sort_by_host_speed(hosts, log)

            for host in hosts:
                url_with_host = "http://" + host["ip"] + ":" + str(
                    host["port"]) + url
                log.info("try to fetch from %s " % url_with_host)
                try:
                    response = urllib2.urlopen(url_with_host)
                    html = response.read()
                    if 'Error' not in html:
                        pkg_download_link = html.strip().decode('utf-8')
                        return pkg_download_link
                    else:
                        log.info('package is not found in ' + host["name"])
                except Exception as err:
                    log.info(err)

            raise EnvironmentError('package not found in all host')

    class VerifyState(State):
        def next(self, args):
            hosts = self.HostState.get_hosts()
            pass
            # try:
            #     response = urllib2.urlopen(self.url + '.md5')
            #     md5 = response.read()
            #     print md5
            # except urllib2.HTTPError, e:
            #     print(e.code)
            # except urllib2.URLError, e:
            #     print(e.args)

    class DownloadState(State):
        def download(self, local_file_path):
            f = urllib2.urlopen(self.url)
            with open(local_file_path, 'wb') as local_file:
                shutil.copyfileobj(f, local_file)

        def generate_local_file_path(self, args):
            file_name = self.url.split("/")[-1]
            if not os.path.exists(args.localRepository):
                os.mkdir(args.localRepository)
            local_file_path = os.path.join(args.localRepository, file_name)
            return local_file_path

        @staticmethod
        def print_time_spent(time_elapse, pkg, log):
            """
            print how much time spent and the avg internet speed
            """
            log.info("Finished downloading, it took %s seconds" % time_elapse)
            if time_elapse > 0:
                speed = (os.path.getsize(pkg) / 1024) / time_elapse
                log.info("Average speed: %s kilobytes per second" % speed)

        def next(self, args):
            local_file_path = self.generate_local_file_path(args)

            if os.path.exists(local_file_path):
                return ResultState(local_file_path)
            try:
                args.log.info("Dowloading: %s " % self.url)
                args.log.info("to: %s" % local_file_path)
                start = datetime.now()

                self.download(local_file_path)

                end = datetime.now()
                diff = end - start
                self.print_time_spent(time_elapse=diff.seconds,
                                      pkg=local_file_path, log=args.log)

            except Exception as err:
                raise EnvironmentError(err)

            return ResultState(local_file_path)


def _get_pkg_url(pkg, version, build='', type='splunk', pkg_released=False,
                 fetcher_url='http://r.susqa.com/cgi-bin/splunk_build_fetcher.py'):
    schemes = ['salt:', 'http:', 'https:', 'ftp:', 's3:']
    if any([True for i in schemes if pkg.startswith(i)]):
        pkg_url = pkg  # pkg is set as static url
    else:
        params = {'PLAT_PKG': pkg, 'DELIVER_AS': 'url'}
        if type == 'splunkforwarder':
            params.update({'UF': '1'})
        if pkg_released:
            params.update({'VERSION': version})
        else:
            params.update({'BRANCH': version})
            if build:
                if isinstance(build, int) or build.isdigit():
                    params.update({'P4CHANGE': build})
                else:
                    logger.warn("build '{b}' is not a number!".format(b=build))

        r = requests.get(fetcher_url, params=params)
        if 'Error' in r.text.strip():
            raise salt.exceptions.CommandExecutionError(
                "Fetcher returned an error: {e}, "
                "requested url: {u}".format(
                    e=r.text.strip(), u=r.url))
        pkg_url = r.text.strip()
    return pkg_url


def download(name):
    pass
