include:
  - splunk.indexer

config_license_client:
  splunk:
    - license_client_configured
    # - servers:
  require:
    - sls: splunk.indexer