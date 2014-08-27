include:
  - splunk.common

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
    - require:
      - sls: splunk.common