base:
  'role:indexer-cluster-master':
    - match: grain
    - indexer_cluster

  'role:indexer-cluster-peer':
    - match: grain
    - indexer_cluster

  'role:indexer-cluster-search-head':
    - match: grain
    - indexer_cluster

  'G@role:search-head-cluster-deployer or G@role:search-head-cluster-member or G@role:search-head-cluster-first-captain':
    - match: compound
    - search_head_cluster

  '*':
    - splunk