__author__ = 'cchung'

import os
import requests

# salt
import salt.exceptions


def __virtual__():
    """
    Salt virtual function:
    (http://docs.saltstack.com/en/latest/ref/modules/#virtual-modules)

    :return: True
    :rtype: bool
    """
    return True # always available for now.


def cache_file(source, dest=''):
    """

    :param source:
    :param saltenv:
    :param dest:
    :return:
    """
    # get source file
    dest = dest or __salt__['pillar.get']['system:fs_root']
    schema = ['salt:', 'http:', 'https:', 'ftp:']
    if any([True for i in schema if source.startswith(i)]):
        filename = os.path.basename(source)
        if os.path.isdir(dest):
            local_path = os.path.join(dest, filename)
        else:
            local_path = dest
        if (os.path.exists(local_path) and
            __salt__['cp.hash_file'](source) == __salt__['cp.hash_file'](dest)):
            cached = dest
        else:
            cached = __salt__['cp.get_url'](source, local_path)
    elif source.startswith('s3:'):
        s3_bucket = source.split('/', 3)[2]
        s3_path = source.split('/', 3)[3]
        s3_filename = os.path.basename(s3_path)
        if os.path.isdir(dest):
            local_path = os.path.join(dest, s3_filename)
        else:
            local_path = dest
        ret = __salt__['s3.get'](s3_bucket, s3_path, local_file=local_path)
        success_string = 'Saved to local file:'
        if ret and ret.startswith(success_string):
            cached = ret.split(success_string)[1].strip()
        else:
            raise salt.exceptions.CommandExecutionError(ret)
    elif os.path.exists(source): # locally stored?
        cached = source
    else:
        msg = ("pkg is not available, please check the schema or local dir of"
               "your source '{s}' is correct".format(s=source))
        raise salt.exceptions.CommandExecutionError(msg)
    return cached


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