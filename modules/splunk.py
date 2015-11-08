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
