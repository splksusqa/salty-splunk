include:
  - splunk.indexer

config_search_head_cluster_member:
  splunk:
    - shcluster_member_configured
    - pass4SymmKey: {{ pillar['search_head_cluster']['pass4SymmKey'] }}
    - shcluster_label: {{ pillar['search_head_cluster']['shcluster_label'] }}
    - replication_factor: {{ pillar['search_head_cluster']['replication_factor'] }}
    - replication_port: {{ pillar['search_head_cluster']['replication_port'] }}
    # - conf_deploy_fetch_url:
  require:
    - sls: splunk.indexer

{% if 'indexer-cluster-search-head' not in salt.grains.get('role') %}
config_search_head_cluster_search_peer:
  splunk:
    - search_peer_configured
    # - servers:
  require:
    - splunk: config_member
{% endif %}

{% if grains['os'] == 'Windows' %}
win-fire-wall-replication-port:
  win_firewall:
    - add_rule
    - localport: {{ pillar['search_head_cluster']['replication_port'] }}
    - protocol: tcp
{% endif %}
