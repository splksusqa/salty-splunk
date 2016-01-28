include:
  - splunk.indexer

config_client:
  splunk:
    - deployment_client_configured
    # - server:
  require:
    - sls: splunk.indexer
