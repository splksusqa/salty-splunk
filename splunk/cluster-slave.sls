
set-slave:
  splunk:
    - rest_configured
    - method: post
    - uri: services/cluster/config/config
    - body:
        mode: slave
        master_uri: https://{{ salt['publish.publish']('role:splunk-cluster-master', 'network.ip_addrs', '', 'grain').values()[0][0] }}:{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_splunkd_port', '', 'grain').values()[0] }}
        replication_port://{{ pillar['cluster-slave']['replication_port'] }}: {}


data:
  splunk:
    - data_monitored
    - source: {{ pillar['splunk']['dataset'] }}


app:
  splunk:
    - app_installed
    - source: {{ pillar['splunk']['app'] }}
