import socket
import json
import logging
logger = logging.getLogger(__name__)


def returner(ret):
    """
    return data to splunk instance installed on master

    :param ret:
    :return:
    """
    ip =  __pillar__['monitoring']['splunk_ip'] or __opts__['master_ip']
    port = __pillar__['monitoring']['listen_port']
    scheme = __pillar__['monitoring']['listen_scheme']

    logger.info("Returning data to {scheme}://{ip}:{port}".format(**locals()))
    if scheme.lower() == 'tcp':
        sock = socket.SOCK_STREAM
    elif scheme.lower() == 'udp':
        sock = socket.SOCK_DGRAM
    else:
        raise Exception("Not supported scheme: {s}".format(s=scheme))
    s = socket.socket(socket.AF_INET, sock)
    s.connect((ip, port))
    s.send(json.dumps(ret))
    s.close()
    return ret
