include:
  - splunk.indexer
  - splunk.pip

config_deployer:
  splunk:
    - shcluster_deployer_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - shcluster_label: {{ pillar['shcluster_label'] }}
  require:
    - sls: [splunk.indexer, splunk.pip]
