include:
  - splunk.indexer

config_search_peer:
  splunk:
    - search_peer_configured
    # - servers:
  require:
    - sls: splunk.indexer