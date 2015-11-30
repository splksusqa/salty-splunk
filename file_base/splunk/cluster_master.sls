include:
  - splunk.indexer
  - splunk.pip

config_master:
  splunk:
    - cluster_master_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - replication_factor: {{ pillar['replication_factor'] }}
    - search_factor: {{ pillar['search_factor'] }}
  require:
    - sls: [splunk.indexer, splunk.pip]
