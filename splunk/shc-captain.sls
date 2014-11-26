include:
 - splunk.common

set-shc:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        replication_port://39997: {}
        shclustering:
          disabled: '0'
          mgmt_uri: https://{{ grains['host']}}:{{ pillar['splunk']['splunkd_port'] }}
          pass4SymmKey: 'pass'
    - restart_splunk: True

wait:
  cmd.run:
    - name: 'sleep 30'


bootstrap-shc:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/shcluster/member/consensus/foo/bootstrap


add-members:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/shcluster/member/consensus/foo
    - body:
        shc_cluster_configuration_id: 1
        shc_new_servers: "{{ salt['publish.publish']('role:splunk-shc-*', 'splunk.get_mgmt_uri', '', 'grain').values()|join(",") }}"