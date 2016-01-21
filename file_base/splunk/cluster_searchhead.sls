include:
  - splunk.indexer
  - splunk.pip

config_searchhead:
  splunk:
    - cluster_searchhead_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    # - master_uri:
    # available values: ip + port, ex."127.0.0.1:8089"
  require:
    - sls: [splunk.indexer, splunk.pip]
