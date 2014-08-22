set-master:
  splunk:
    - rest_configured
    - method: post
    - uri: services/cluster/config/config
    - body:
        mode: master
        replication_factor: 2
        search_factor: 1