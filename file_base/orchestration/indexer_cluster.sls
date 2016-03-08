# salt-run state.orch orchestration.cluster

master_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-master'
    - tgt_type: grain
    - sls: splunk.cluster_master

slave_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-slave'
    - tgt_type: grain
    - sls: splunk.cluster_slave
    - require:
      - salt: master_setup

searchhead_setup:
  salt.state:
    - tgt: 'role:indexer-cluster-search-head'
    - tgt_type: grain
    - sls: splunk.cluster_searchhead
    - require:
      - salt: master_setup