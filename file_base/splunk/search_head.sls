include:
  - splunk.indexer

# For dmc, we need to forward internal logs of search heads to indexers
add-forward-server:
  splunk:
    - forward_servers_added

{% if 'indexer-cluster-search-head' not in salt.grains.get('role') %}
config_search_peer:
  splunk:
    - search_peer_configured
    # - servers:
  require:
    - sls: splunk.indexer
{% endif %}