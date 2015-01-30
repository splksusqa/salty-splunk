# salt-run state.orch orchestration.all

dist-idx:
  salt.state:
    - tgt: 'role:splunk-indexer'
    - tgt_type: grain
    - sls: splunk.indexer

master_setup:
  salt.state:
    - tgt: 'role:splunk-cluster-master'
    - tgt_type: grain
    - sls: splunk.cluster-master

slave_setup:
  salt.state:
    - tgt: 'role:splunk-cluster-slave'
    - tgt_type: grain
    - sls: splunk.cluster-slave
    - require:
      - salt: master_setup

searchhead_setup:
  salt.state:
    - tgt: 'role:splunk-cluster-searchhead'
    - tgt_type: grain
    - sls: splunk.cluster-searchhead
    - require:
      - salt: master_setup

dist-sh:
  salt.state:
    - tgt: 'role:splunk-searchhead'
    - tgt_type: grain
    - sls: splunk.searchhead
    - require:
      - salt: dist-idx

shc-deployer:
  salt.state:
    - tgt: 'role:splunk-shc-deployer'
    - tgt_type: grain
    - sls: splunk.shc-deployer

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
