base:
  'role:search-head':
    - match: grain
    - splunk.search_head

  'role:indexer':
    - match: grain
    - splunk.indexer

  'role:indexer-cluster-master':
    - match: grain
    - splunk.indexer_cluster_master

  'role:indexer-cluster-peer':
    - match: grain
    - splunk.indexer_cluster_peer

  'role:indexer-cluster-search-head':
    - match: grain
    - splunk.indexer_cluster_search_head

  'role:search-head-cluster-deployer':
    - match: grain
    - splunk.shcluster_deployer

  'role:search-head-cluster-member':
    - match: grain
    - splunk.shcluster_member

  'role:search-head-cluster-first-captain':
    - match: grain
    - splunk.shcluster_captain

  'role:central-license-master':
    - match: grain
    - splunk.central_license_master

  'role:central-license-slave':
    - match: grain
    - splunk.central_license_slave

  'role:deployment-client':
    - match: grain
    - splunk.deployment_client

  'role:universal-forwarder':
    - match: grain
    - splunk.uf

  'role:deployment-server':
    - match: grain
    - splunk.indexer

  'role:search-head-pooling-shared-storage':
    - match: grain
    - splunk.shp_shared_storage

  'role:search-head-pooling-member':
    - match: grain
    - splunk.shp_member
