# salt-run state.orch orchestration.searchhead_cluster

deployer_setup:
  salt.state:
    - tgt: 'role:splunk-shcluster-deployer'
    - tgt_type: grain
    - sls: splunk.shcluster_deployer

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