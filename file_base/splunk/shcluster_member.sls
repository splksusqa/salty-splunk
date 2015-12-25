include:
  - splunk.indexer
  - splunk.pip

config_member:
  splunk:
    - shcluster_member_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - shcluster_label: {{ pillar['shcluster_label'] }}
    - replication_factor: {{ pillar['replication_factor'] }}
    - replication_port: {{ pillar['replication_port'] }}
    - conf_deploy_fetch_url: "{{ salt['publish.publish']('role:splunk-shcluster-deployer', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"

config_search_peer:
  splunk:
    - search_peer_configured
    - servers: "{{ salt['publish.publish']('role:splunk-shcluster-indexer', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
  require:
    - sls: [splunk.indexer, splunk.pip]
