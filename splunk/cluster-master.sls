set-cluster:
  splunk:
    - set_role
    - method: conf
    - conf: server.conf
    - setting:
        clustering:
          mode: master
