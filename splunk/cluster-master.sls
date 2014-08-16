set-cluster:
  splunk:
    - role_configured
    - method: conf
    - conf: server.conf
    - setting:
        clustering:
          mode: master

set_role:
  splunk:
    - rest_configured
    - method: post
    - uri: services/cluster/config/config
    - body:
        mode: master
        replication_factor: 2
        search_factor: 1