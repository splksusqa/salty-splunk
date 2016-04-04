include:
  - splunk.indexer

# dummy for avoiding empty sls if skipping below configuration
always-passes:
  test.succeed_without_changes:
    - name: foo

{% if 'indexer-cluster-search-head' not in salt.grains.get('role') %}
config_search_peer:
  splunk:
    - search_peer_configured
    # - servers:
  require:
    - sls: splunk.indexer
{% endif %}