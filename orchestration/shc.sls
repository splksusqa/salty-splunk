# salt-run state.orch orchestration.cluster

# salt-run state.orch orchestration.cluster

shc-member:
  salt.state:
    - tgt: 'role:*splunk-shc-member'
    - tgt_type: grain
    - sls: splunk.shc-member

shc-captain:
  salt.state:
    - tgt: 'role:*splunk-shc-captain'
    - tgt_type: grain
    - sls: splunk.shc-captain
