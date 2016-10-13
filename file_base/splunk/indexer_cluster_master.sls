include:
  - splunk.indexer

config_master:
  splunk:
    - cluster_master_configured
    - pass4SymmKey: {{ pillar['indexer_cluster']['pass4SymmKey'] }}
    - replication_factor: {{ pillar['indexer_cluster']['replication_factor'] }}
    - search_factor: {{ pillar['indexer_cluster']['search_factor'] }}
    - cluster_label: {{ pillar['indexer_cluster']['cluster_label'] }}
    - site_replication_factor: {{ pillar['indexer_cluster']['site_replication_factor'] }}
    - site_search_factor: {{ pillar['indexer_cluster']['site_search_factor'] }}
    - number_of_sites: {{ pillar['indexer_cluster']['number_of_sites'] }}
  require:
    - sls: splunk.indexer
