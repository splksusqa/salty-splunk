# salt-run state.orch orchestration.cluster

shc-member:
  salt.state:
    - tgt: 'role:splunk-shc-member'
    - tgt_type: grain
    - sls: splunk.shc-member

shc-captain:
  salt.state:
    - tgt: 'role:splunk-shc-captain'
    - tgt_type: grain
    - sls: splunk.shc-captain
    - require:
      - salt: shc-member

add-searchpeer:
  salt.state:
    - tgt: 'role:splunk-shc-member'
    - tgt_type: grain
    - sls: splunk.shc-add-searchpeer
    - require:
      - salt: shc-captain