# salt-run state.orch orchestration.single

indexer_setup:
  salt.state:
    - tgt: 'role:splunk-single-indexer'
    - tgt_type: grain
    - sls: splunk.indexer