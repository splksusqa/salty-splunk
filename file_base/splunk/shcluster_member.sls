include:
  - splunk.indexer

config_member:
  splunk:
    - shcluster_member_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - shcluster_label: {{ pillar['shcluster_label'] }}
    - replication_factor: {{ pillar['replication_factor'] }}
    - replication_port: {{ pillar['replication_port'] }}
    # - conf_deploy_fetch_url:
  require:
    - sls: splunk.indexer


config_search_peer:
  splunk:
    - search_peer_configured
    # - servers:
  require:
    - sls: splunk.indexer
