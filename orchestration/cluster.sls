# salt-run state.orch orchestration.cluster

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