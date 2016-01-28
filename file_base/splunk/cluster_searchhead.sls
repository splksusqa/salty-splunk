include:
  - splunk.indexer

config_searchhead:
  splunk:
    - cluster_searchhead_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    # - master_uri:
  require:
    - sls: splunk.indexer
