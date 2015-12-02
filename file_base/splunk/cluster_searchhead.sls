include:
  - splunk.indexer
  - splunk.pip

config_searchhead:
  splunk:
    - cluster_searchhead_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
  require:
    - sls: [splunk.indexer, splunk.pip]
