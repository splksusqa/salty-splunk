include:
  - splunk.indexer

config_slave:
  splunk:
    - cluster_slave_configured
    - pass4SymmKey: {{ pillar['indexer_cluster']['pass4SymmKey'] }}
    - replication_port: {{ pillar['indexer_cluster']['replication_port'] }}
    # - master_uri:
  require:
    - sls: splunk.indexer

{% if grains['os'] == 'Windows' %}
SplunkReplicationPort:
  win_firewall:
    - add_rule
    - localport: {{ pillar['indexer_cluster']['replication_port'] }}
    - protocol: tcp
{% endif %}