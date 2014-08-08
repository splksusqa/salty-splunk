
app:
  splunk:
    - app_installed
    - source: {{ pillar['splunk']['app_source'] }} # s3://
    - dest: {{ pillar['splunk']['app_dest'] }}

set-cluster:
  splunk:
    - set_role
    - method: conf
    - conf: server.conf
    - setting:
        clustering:
          mode: slave
          master_uri: https://{{ salt['publish.publish']('role:splunk-cluster-master', 'network.ip_addrs', '', 'grain').values()[0][0] }}:{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_splunkd_port', '', 'grain').values()[0] }}
        replication_port://{{ pillar['cluster-slave']['replication_port'] }}: {}

data:
  splunk:
    - data_indexed
    - source: {{ pillar['splunk']['dataset_source'] }} # s3://
    - dest: {{ pillar['splunk']['dataset_dest'] }} # /tmp/dest.log

