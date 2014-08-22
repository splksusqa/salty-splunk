__author__ = 'cchung'
import socket
import json

def returner(ret):
    """
    return data to splunk instance installed on master

    :param ret:
    :return:
    """
    ip =  __pillar__['monitoring']['splunk_ip'] or __opts__['master_ip']
    port = __pillar__['monitoring']['listen_port']
    schema = __pillar__['monitoring']['listen_schema']

    if schema.lower() == 'tcp':
        sock = socket.SOCK_STREAM
    elif schema.lower() == 'udp':
        sock = socket.SOCK_DGRAM
    else:
        raise Exception("Not supported schema {s}".format(s=schema))

    s = socket.socket(socket.AF_INET, sock)
    s.connect((ip, port))
    s.send(json.dumps(ret))
    s.close()
    return ret