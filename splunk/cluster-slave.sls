set-cluster:
  splunk:
    - set_role
    - method: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: slave
          master_uri: https://{{ salt['publish.publish']('role:splunk-cluster-master', 'network.ip_addrs', '', 'grain').values()[0][0] }}:{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.splunkd_port', '', 'grain').values()[0] }}
        replication_port://{{ pillar['cluster-slave']['replication_port'] }}: {}