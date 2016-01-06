include:
  - splunk.indexer

config_member:
  splunk:
    - shcluster_member_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - shcluster_label: {{ pillar['shcluster_label'] }}
    - replication_factor: {{ pillar['replication_factor'] }}
    - replication_port: {{ pillar['replication_port'] }}
    - conf_deploy_fetch_url: "{{ salt['publish.publish']('role:splunk-shcluster-deployer', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"

config_searchhead:
  splunk:
    - cluster_searchhead_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
  require:
    - sls: splunk.indexer
