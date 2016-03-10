include:
  - splunk.indexer

config_slave:
  splunk:
    - cluster_slave_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - replication_port: {{ pillar['replication_port'] }}
    # - master_uri:
  require:
    - sls: splunk.indexer

{% if grains['os'] == 'Windows' %}
SplunkReplicationPort:
  win_firewall:
    - add_rule
    - localport: {{ pillar['replication_port'] }}
    - protocol: tcp
{% endif %}