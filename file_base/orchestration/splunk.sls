# salt-run state.orch orchestration.searchhead_and_indexer_cluster

# 1 simple indexer
indexer_setup:
  salt.state:
    - tgt: 'role:indexer'
    - tgt_type: grain
    - sls: splunk.indexer
    - order: 1

# 2 SHC
search_head_deployer_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-deployer'
    - tgt_type: grain
    - sls: splunk.shcluster_deployer
    - order: 2

search_head_member_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-member'
    - tgt_type: grain
    - sls: splunk.cluster_shcluster_member
    - require:
      - salt: search_head_deployer_setup

search_head_captain_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-first-captain'
    - tgt_type: grain
    - sls: splunk.shcluster_captain
    - require:
      - salt: search_head_member_setup

# 3 IDX cluster
indexer_cluster_master_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-master'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_master
    - order: 3

indexer_cluster_peer_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-peer'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_peer
    - require:
      - salt: indexer_cluster_master_setup

indexer_cluster_search_head_setup:
  salt.state:
    - tgt: 'role:indexer_cluster_search_head'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_search_head
    - require:
      - salt: indexer_cluster_master_setup

# 4 Simple search head
distributed_search_head_setup:
  salt.state:
    - tgt: 'role:search_head'
    - tgt_type: grain
    - sls: splunk.search_head
    - order: 4

# 5 Central license master and slave
central_license_master_setup:
  salt.state:
    - tgt: 'role:central-license-master'
    - tgt_type: grain
    - sls: splunk.central_license_master
    - order: 5

central_license_slave_setup:
  salt.state:
    - tgt: 'role:central-license-slave'
    - tgt_type: grain
    - sls: splunk.central_license_slave
    - require:
      - salt: central_license_master_setup

# 6 Deployment server
# deployment sever don't need configuration

deployment_client_setup:
  salt.state:
    - tgt: 'role:deployment-client'
    - tgt_type: grain
    - sls: splunk.deployment_client
    - order: 6

# 7 Universal forwarder

universal_forwarder_setup:
  salt.state:
    - tgt: 'role:universal-forwarder'
    - tgt_type: grain
    - sls: splunk.uf
    - order: 7