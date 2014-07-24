install-splunk:
  splunk:
    - installed
    - source: {{ pillar['splunk']['pkg'] }}
    - installer_flags: {{ pillar['installer_flags'] }}
    - splunk_home: {{ pillar['splunk']['home'] }}


set-cluster:
  splunk:
    - set_role
    - mode: cluster-slave
    - master: {{ salt['publish.publish']('*cluster-master*', 'network.ip_addrs').values()[0][0] }}:8089
    - replication_port: 8888