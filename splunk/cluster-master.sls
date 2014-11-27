include:
  - splunk.common

#set-master:
#  splunk:
#    - configured
#    - interface: rest
#    - method: post
#    - uri: services/cluster/config/config
#    - body:
#        mode: master
#        replication_factor: '2'
#        search_factor: '1'
#    - require:
#      - sls: splunk.common

set-master:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: master
          replication_factor: '2'
          search_factor: '1'
    - restart_splunk: True
    - require:
      - sls: splunk.common