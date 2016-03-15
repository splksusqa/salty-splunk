include:
  - splunk.indexer

config_master:
  splunk:
    - cluster_master_configured
    - pass4SymmKey: {{ pillar['indexer_cluster']['pass4SymmKey'] }}
    - replication_factor: {{ pillar['indexer_cluster']['replication_factor'] }}
    - search_factor: {{ pillar['indexer_cluster']['search_factor'] }}
  require:
    - sls: splunk.indexer
