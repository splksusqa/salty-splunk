__author__ = 'cchung'

import os
import errno
import requests
import logging

# salt
import salt.exceptions
logger = logging.getLogger(__name__)


def __virtual__():
    """
    Salt virtual function:
    (http://docs.saltstack.com/en/latest/ref/modules/#virtual-modules)

    :return: True
    :rtype: bool
    """
    return True  # always available for now.


def cache_file(source, dest='', user=''):
    """

    :param source:
    :param dest:
    :return:
    """
    # get source file
    dest = dest or __salt__['pillar.get']('system:files_dir')
    user = user or __salt__['pillar.get']('system:user')
    schemes = ['salt:', 'http:', 'https:', 'ftp:', 's3:']
    logger.info("Caching file from '{source}' to '{dest}', user={user}".format(
                **locals()))
    if any([True for scheme in schemes if source.startswith(scheme)]):
        filename = os.path.basename(source)
        if dest.endswith(os.sep) or os.path.isdir(dest):
            mkdirs(dest)
            local_path = os.path.join(dest, filename)
        else:
            mkdirs(os.path.dirname(dest))
            local_path = dest

        if source.startswith('s3:'):
            # not check hash from s3, so download it anyway.
            s3_bucket = source.split('/', 3)[2]
            s3_path = source.split('/', 3)[3]
            logger.info("File is stored at s3, usning s3.get module")
            ret = __salt__['s3.get'](s3_bucket, s3_path, local_file=local_path)
            success_string = 'Saved to local file:'
            if ret and ret.startswith(success_string):
                cached = local_path
            else:
                raise salt.exceptions.CommandExecutionError(
                    "Failed to get s3 file, ret={r}".format(r=ret))
        elif os.path.exists(local_path) and (
                 __salt__['cp.hash_file'](source) ==
                 __salt__['cp.hash_file'](local_path)):
            logger.info("Local file {local_path} has same hash with {source}, "
                        "not fetching again.".format(**locals()))
            cached = local_path
        else:
            logger.info("Fetching file using cp.get_url module")
            cached = __salt__['cp.get_url'](source, local_path)
    elif os.path.exists(source):  # locally path?
        logger.info("File is locally stored.")
        cached = source
    else:
        msg = ("file is unavailable, please check the scheme or local path of "
               "your source '{source}' is correct".format(**locals()))
        raise salt.exceptions.CommandExecutionError(msg)
    __salt__['file.chown'](cached, user, user)
    return cached


def mkdirs(path):
    """

    :param path:
    :return:
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def instance_data(data='', url='http://instance-data/latest/meta-data/'):
    """

    :param data:
    :param url:
    :return:
    """
    return requests.get(url+data).content


def public_ip():
    """

    :return:
    """
    return instance_data(data='public-ipv4')


def private_ip():
    """

    :return:
    """
    return instance_data(data='local-ipv4')

