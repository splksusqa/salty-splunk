include:
  - splunk.indexer
  - splunk.pip

config_slave:
  splunk:
    - cluster_slave_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - master_uri: qasus-ubu1404x64-002:8089
    - replication_port: {{ pillar['replication_port'] }}
  require:
    - sls: [splunk.indexer, splunk.pip]
