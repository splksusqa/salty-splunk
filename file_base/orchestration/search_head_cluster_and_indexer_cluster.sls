# salt-run state.orch orchestration.searchhead_and_indexer_cluster

master_setup:
  salt.state:
    - tgt: 'role:splunk-cluster-master'
    - tgt_type: grain
    - sls: splunk.cluster_master

slave_setup:
  salt.state:
    - tgt: 'role:splunk-cluster-slave'
    - tgt_type: grain
    - sls: splunk.cluster_slave
    - require:
      - salt: master_setup

deployer_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-deployer'
    - tgt_type: grain
    - sls: splunk.shcluster_deployer
    - require:
      - salt: master_setup

member_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-member'
    - tgt_type: grain
    - sls: splunk.cluster_shcluster_member
    - require:
      - salt: deployer_setup

captain_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-captain'
    - tgt_type: grain
    - sls: splunk.shcluster_captain
    - require:
      - salt: member_setup