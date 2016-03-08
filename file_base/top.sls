# Using 'id' for now, but better way of specifying nodes is by its 'role'

base:
  'role:search-head':
    - match: grain
    - splunk.indexer_cluster_master

  'role:indexer-cluster-master':
    - match: grain
    - splunk.cluster_slave

  'role:indexer-cluster-search-head':
    - match: grain
    - splunk.cluster_search_head

  'role:indexer-cluster-master':
    - match: grain
    - splunk.cluster_searchhead

  'role:search-head-cluster-member':
    - match: grain
    - splunk.shcluster_captain

  'role:search-head-cluster-deployer':
    - match: grain
    - splunk.shcluster_deployer

  role:search-head-cluster-first-captain:
    - match: grain
    - splunk.shcluster_member

  role:deployment-client:
    - match: grain
    - splunk.deployment_client

