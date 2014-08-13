
set-cluster:
  splunk:
    - role_as
    - method: conf
    - conf: server.conf
    - setting:
        clustering:
          mode: slave
          master_uri: https://{{ salt['publish.publish']('role:splunk-cluster-master', 'network.ip_addrs', '', 'grain').values()[0][0] }}:{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_splunkd_port', '', 'grain').values()[0] }}
        replication_port://{{ pillar['cluster-slave']['replication_port'] }}: {}


data:
  splunk:
    - data_monitored
    - source: {{ pillar['splunk']['dataset_source'] }}
    - dest: {{ pillar['splunk']['dataset_dest'] }}


app:
  splunk:
    - app_installed
    - source: {{ pillar['splunk']['app_source'] }}
    - dest: {{ pillar['splunk']['app_dest'] }}
