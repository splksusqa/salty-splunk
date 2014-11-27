include:
  - splunk.common

#set-searchhead:
#  splunk:
#    - configured
#    - interface: rest
#    - method: post
#    - uri: services/cluster/config/config
#    - body:
#        mode: searchhead
#        master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
#    - require:
#      - sls: splunk.common

set-searchhead:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: searchhead
          master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
    - restart_splunk: True
    - require:
      - sls: splunk.common