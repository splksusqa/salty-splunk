base:
  'G@role:indexer-cluster-master or G@role:indexer-cluster-peer or G@role:indexer-cluster-search-head':
    - match: compound
    - indexer_cluster

  'G@role:search-head-cluster-deployer or G@role:search-head-cluster-member or G@role:search-head-cluster-first-captain':
    - match: compound
    - search_head_cluster

  '*':
    - splunk