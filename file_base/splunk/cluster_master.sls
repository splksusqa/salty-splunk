include:
  - splunk.indexer
  - splunk.pip

config_master:
  splunk:
    - cluster_master_configured
    - pass4SymmKey: 123
    - replication_factor: 3
    - search_factor: 3
  require:
    - sls: [splunk.indexer, splunk.pip]