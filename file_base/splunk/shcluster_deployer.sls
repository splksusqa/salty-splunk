include:
  - splunk.indexer

config_deployer:
  splunk:
    - shcluster_deployer_configured
    - pass4SymmKey: {{ pillar['search_head_cluster']['pass4SymmKey'] }}
    - shcluster_label: {{ pillar['search_head_cluster']['shcluster_label'] }}
  require:
    - sls: splunk.indexer
