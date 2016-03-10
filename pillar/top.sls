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

  'role:search-head-cluster-deployer':
    - match: grain
    - searchhead_cluster

  'role:search-head-cluster-member':
    - match: grain
    - searchhead_cluster

  'role:search-head-cluster-first-captain':
    - match: grain
    - searchhead_cluster

  '*':
    - splunk