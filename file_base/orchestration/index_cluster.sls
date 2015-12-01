# salt-run state.orch orchestration.cluster

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