# salt-run state.orch orchestration.searchhead_cluster

indexer_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-indexer'
    - tgt_type: grain
    - sls: splunk.indexer

deployer_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-deployer'
    - tgt_type: grain
    - sls: splunk.shcluster_deployer
    - require:
      - salt: indexer_setup

member_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-member'
    - tgt_type: grain
    - sls: splunk.shcluster_member
    - require:
      - salt: deployer_setup

captain_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-captain'
    - tgt_type: grain
    - sls: splunk.shcluster_captain
    - require:
      - salt: member_setup
