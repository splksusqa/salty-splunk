# salt-run state.orch orchestration.searchhead_and_indexer_cluster

# install every Enterprise to accelerate the orchestration
# 1 simple indexer, every role except uf is simple indexer at first
indexer_setup:
  salt.state:
    - tgt: 'not G@role:universal-forwarder'
    - tgt_type: compound
    - sls: splunk.indexer
    - order: 1

# 2 SHC
search_head_deployer_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-deployer'
    - tgt_type: grain
    - sls: splunk.shcluster_deployer
    - order: 2
    - require:
      - salt: indexer_setup

search_head_member_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-member'
    - tgt_type: grain
    - sls: splunk.shcluster_member
    - order: 2
    - require:
      - salt: search_head_deployer_setup

search_head_captain_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-first-captain'
    - tgt_type: grain
    - sls: splunk.shcluster_captain
    - order: 2
    - require:
      - salt: search_head_member_setup

# 3 IDX cluster
indexer_cluster_master_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-master'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_master
    - order: 3
    - require:
      - salt: indexer_setup
      - salt: search_head_deployer_setup

indexer_cluster_peer_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-peer'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_peer
    - order: 3
    - require:
      - salt: indexer_cluster_master_setup

indexer_cluster_search_head_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-search-head'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_search_head
    - order: 3
    - require:
      - salt: indexer_cluster_master_setup

# 4 Simple search head
distributed_search_head_setup:
  salt.state:
    - tgt: 'role:search-head'
    - tgt_type: grain
    - sls: splunk.search_head
    - order: 4
    - require:
      - salt: indexer_setup
      - salt: indexer_cluster_master_setup
      - salt: indexer_cluster_peer_setup
      - salt: indexer_cluster_search_head_setup

# 5 SHP
search_head_pooling_share_storage_setup:
  salt.state:
    - tgt: 'role:search-head-pooling-shared-storage'
    - tgt_type: grain
    - sls: splunk.shp_share_storage
    - order: 5
    - require:
      - salt: indexer_setup

search_head_pooling_member_setup:
  salt.state:
    - tgt: 'role:search-head-pooling-member'
    - tgt_type: grain
    - sls: splunk.shp_member
    - order: 5
    - batch: 1
    - require:
      - salt: search_head_pooling_share_storage_setup

# 6 Central license master and slave
central_license_master_setup:
  salt.state:
    - tgt: 'role:central-license-master'
    - tgt_type: grain
    - sls: splunk.central_license_master
    - order: 6
    - require:
      - salt: indexer_setup
      - salt: distributed_search_head_setup

central_license_slave_setup:
  salt.state:
    - tgt: 'role:central-license-slave'
    - tgt_type: grain
    - sls: splunk.central_license_slave
    - order: 6
    - require:
      - salt: central_license_master_setup

# 7 Universal forwarder
universal_forwarder_setup:
  salt.state:
    - tgt: 'role:universal-forwarder'
    - tgt_type: grain
    - sls: splunk.uf
    - order: 7

# 8 Deployment server
# deployment sever don't need configuration
deployment_server_setup:
  salt.state:
    - tgt: 'role:deployment-server'
    - tgt_type: grain
    - sls: splunk.indexer
    - order: 8
    - require:
      - salt: indexer_setup
      - salt: central_license_master_setup
      - salt: central_license_slave_setup

deployment_client_setup:
  salt.state:
    - tgt: 'role:deployment-client'
    - tgt_type: grain
    - sls: splunk.deployment_client
    - order: 8
    - require:
      - salt: deployment_server_setup

# 9
dmc_setup:
  salt.state:
    - tgt: 'role:distributed-management-console'
    - tgt_type: grain
    - sls: splunk.distributed_management_console
    - order: 9
