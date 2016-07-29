include:
  - splunk.indexer

config_searchhead:
  splunk:
    - cluster_searchhead_configured
    - pass4SymmKey: {{ pillar['indexer_cluster']['pass4SymmKey'] }}
    - cluster_label: {{ pillar['indexer_cluster']['cluster_label']}}
    # - master_uri:
  require:
    - sls: splunk.indexer