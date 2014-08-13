set-cluster:
  splunk:
    - role_as
    - method: conf
    - conf: server.conf
    - setting:
        clustering:
          mode: master
