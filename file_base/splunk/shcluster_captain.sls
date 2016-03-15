include:
  - splunk.indexer

bootstrap_captain:
  splunk:
    - shcluster_captain_bootstrapped
    # - servers_list:
  require:
    - sls: splunk.indexer
