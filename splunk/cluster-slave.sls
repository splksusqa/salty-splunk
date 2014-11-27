include:
  - splunk.common

#set-slave:
#  splunk:
#    - configured
#    - interface: rest
#    - method: post
#    - uri: services/cluster/config/config
#    - body:
#        mode: slave
#        master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
#        replication_port: "{{ pillar['cluster-slave']['replication_port'] }}"
#    - require:
#      - sls: splunk.common


set-slave:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: slave
          master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
        replication_port://{{ pillar['cluster-slave']['replication_port'] }}: {}
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
        name: 9996
    - require:
      - sls: splunk.common


listen_tcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/raw
    - body:
        name: 9997
    - require:
      - sls: splunk.common


listen_udp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/udp
    - body:
        name: 9998
    - require:
      - sls: splunk.common

# if you'd like to use the following states, remember to put aws keys
# since they're using data/app from s3 buckets
#data:
#  splunk:
#    - data_monitored
#    - source: {{ pillar['splunk']['dataset'] }}
#    - require:
#      - sls: splunk.common
#
#
#app:
#  splunk:
#    - app_installed
#    - source: {{ pillar['splunk']['app'] }}
#    - require:
#      - sls: splunk.common