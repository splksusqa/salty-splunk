include:
  - splunk.common

set-slave:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: slave
          master_uri: https://{{ salt['publish.publish']('role:splunk-cluster-master', 'network.ip_addrs', '', 'grain').values()[0][0] }}:{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_splunkd_port', '', 'grain').values()[0] }}
        replication_port://{{ pillar['cluster-slave']['replication_port'] }}: {}
    - require:
      - sls: splunk.common

data:
  splunk:
    - data_monitored
    - source: {{ pillar['splunk']['dataset'] }}
    - require:
      - sls: splunk.common

app:
  splunk:
    - app_installed
    - source: {{ pillar['splunk']['app'] }}
    - require:
      - sls: splunk.common