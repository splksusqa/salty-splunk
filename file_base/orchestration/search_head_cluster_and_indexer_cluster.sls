# salt-run state.orch orchestration.searchhead_and_indexer_cluster

master_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-master'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_master

slave_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-peer'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_peer
    - require:
      - salt: master_setup

deployer_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-deployer'
    - tgt_type: grain
    - sls: splunk.shcluster_deployer
    - require:
      - salt: master_setup

member_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-member'
    - tgt_type: grain
    - sls: splunk.cluster_shcluster_member
    - require:
      - salt: deployer_setup

captain_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-first-captain'
    - tgt_type: grain
    - sls: splunk.shcluster_captain
    - require:
      - salt: member_setup

indexer_cluster_search_head_setup:
  salt.state:
    - tgt: 'role:search-head-cluster-search-head'
    - tgt_type: grain
    - sls: splunk.indexer_cluster_search_head
    - require:
      - salt: captain_setup