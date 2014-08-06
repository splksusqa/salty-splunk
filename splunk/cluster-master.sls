set-cluster:
  splunk:
    - set_role
    - method: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: master
