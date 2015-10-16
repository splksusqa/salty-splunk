include:
  - splunk.common


set_retention:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/system/data/indexes/main
    - body:
        maxTotalDataSizeMB: {{ pillar['retention']['maxTotalDataSizeMB'] }}
        maxWarmDBCount:     {{ pillar['retention']['maxWarmDBCount'] }}
        maxDataSize:        {{ pillar['retention']['maxDataSize'] }}
    - require:
      - sls: splunk.common


set-slave:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: slave
          master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
        replication_port://{{ pillar['idx-replication']['port'] }}: {}
    - restart_splunk: True
    - require:
      - sls: splunk.common


listen_splunktcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/cooked
    - body:
        name: {{ pillar['listen_port']['splunktcp'] }}
    - require:
      - sls: splunk.common


listen_tcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/raw
    - body:
        name: {{ pillar['listen_port']['tcp'] }}
    - require:
      - sls: splunk.common


listen_udp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/udp
    - body:
        name: {{ pillar['listen_port']['udp'] }}
    - require:
      - sls: splunk.common


data:
  splunk:
    - data_monitored
    - source: {{ pillar['dataset']['1m'] }}
    - require:
      - sls: splunk.common


app:
  splunk:
    - app_installed
    - source: {{ pillar['app']['gendata'] }}
    - require:
      - sls: splunk.common

