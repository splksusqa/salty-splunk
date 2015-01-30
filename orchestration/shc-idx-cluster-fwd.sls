# salt-run state.orch orchestration.shc-idx-cluster-fwd

master_setup:
  salt.state:
    - tgt: 'role:*splunk-cluster-master'
    - tgt_type: grain
    - sls: splunk.cluster-master

slave_setup:
  salt.state:
    - tgt: 'role:*splunk-cluster-slave'
    - tgt_type: grain
    - sls: splunk.cluster-slave
    - require:
      - salt: master_setup

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

uf-setup:
  salt.state:
    - tgt: 'role:splunk-universal-fwd'
    - tgt_type: grain
    - sls: splunk.universal-fwd
    - require:
      - salt: slave_setup
