# salt-run state.orch orchestration.all

lic-master-setup:
  salt.state:
    - tgt: 'role:splunk-lic-master'
    - tgt_type: grain
    - sls: splunk.lic-master

deployment-server-setup:
  salt.state:
    - tgt: 'role:splunk-deployment-server'
    - tgt_type: grain
    - sls: splunk.deployment-server

dist-idx-setup:
  salt.state:
    - tgt: 'role:splunk-indexer'
    - tgt_type: grain
    - sls: splunk.indexer

cluster-master-setup:
  salt.state:
    - tgt: 'role:splunk-cluster-master'
    - tgt_type: grain
    - sls: splunk.cluster-master

cluster-slave-setup:
  salt.state:
    - tgt: 'role:splunk-cluster-slave'
    - tgt_type: grain
    - sls: splunk.cluster-slave
    - require:
      - salt: cluster-master-setup

cluster-searchhead-setup:
  salt.state:
    - tgt: 'role:splunk-cluster-searchhead'
    - tgt_type: grain
    - sls: splunk.cluster-searchhead
    - require:
      - salt: cluster-master-setup

dist-sh-setup:
  salt.state:
    - tgt: 'role:splunk-searchhead'
    - tgt_type: grain
    - sls: splunk.searchhead
    - require:
      - salt: dist-idx-setup

shc-deployer-setup:
  salt.state:
    - tgt: 'role:splunk-shc-deployer'
    - tgt_type: grain
    - sls: splunk.shc-deployer

shc-member-setup:
  salt.state:
    - tgt: 'role:splunk-shc-member'
    - tgt_type: grain
    - sls: splunk.shc-member

shc-captain-setup:
  salt.state:
    - tgt: 'role:splunk-shc-captain'
    - tgt_type: grain
    - sls: splunk.shc-captain
    - require:
      - salt: shc-member-setup

shc-add-searchpeer:
  salt.state:
    - tgt: 'role:splunk-shc-member'
    - tgt_type: grain
    - sls: splunk.shc-add-searchpeer
    - require:
      - salt: shc-captain-setup

heavy-fwd-setup:
  salt.state:
    - tgt: 'role:splunk-heavy-fwd'
    - tgt_type: grain
    - sls: splunk.heavy-fwd

light-fwd-setup:
  salt.state:
    - tgt: 'role:splunk-light-fwd'
    - tgt_type: grain
    - sls: splunk.light-fwd

universal-fwd-setup:
  salt.state:
    - tgt: 'role:splunk-universal-fwd'
    - tgt_type: grain
    - sls: splunk.universal-fwd

dmc-setup:
  salt.state:
    - tgt: 'role:splunk-dmc'
    - tgt_type: grain
    - sls: splunk.dmc
