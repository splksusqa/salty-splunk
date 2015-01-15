__author__ = 'cchung'

from salt.cloud import CloudClient
import salt.config

def launch(idx, sh, fwd, tag='no_tag', conf=''):
    cc = CloudClient('/etc/salt/cloud')
    profile = "{plat}-{role}-{size}".format(plat=idx['platform'],
                                            role='splunk-indexer',
                                            size=idx['size'])
    cc.profile(profile,
               names=[profile+'-'+str(i) for i in range(int(idx['num']))],
               parallel=True)


def deploy():
    pass

def provision():
    pass

def opt():
    master_opts = salt.config.client_config('/etc/salt/master')
    print master_opts
