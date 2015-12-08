include:
  - splunk.indexer
  - splunk.pip

config_slave:
  splunk:
    - cluster_slave_configured
    - pass4SymmKey: {{ pillar['pass4SymmKey'] }}
    - master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
    - replication_port: {{ pillar['replication_port'] }}
  require:
    - sls: [splunk.indexer, splunk.pip]

{% if grains['os'] == 'Windows' %}
SplunkReplicationPort:
  win_firewall:
    - add_rule
    - localport: {{ pillar['replication_port'] }}
    - protocol: tcp
{% endif %}