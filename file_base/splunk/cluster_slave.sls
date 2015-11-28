include:
  - splunk.indexer
  - splunk.pip

config_slave:
  splunk:
    - cluster_slave_configured
    - pass4SymmKey: 123
    - master_uri: qasus-ubu1404x64-002:8089
    - replication_port: 9999
  require:
    - sls: [splunk.indexer, splunk.pip]
