set-searchhead:
  splunk:
    - rest_configured
    - method: post
    - uri: services/cluster/config/config
    - body:
        mode: searchhead
        master_uri: https://{{ salt['publish.publish']('role:splunk-cluster-master', 'network.ip_addrs', '', 'grain').values()[0][0] }}:{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_splunkd_port', '', 'grain').values()[0] }}
