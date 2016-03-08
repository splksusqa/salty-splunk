# salt-run state.orch orchestration.deployment

server_setup:
  salt.state:
    - tgt: 'role:deployment-server'
    - tgt_type: grain
    - sls: splunk.indexer

client_setup:
  salt.state:
    - tgt: 'role:deployment-client'
    - tgt_type: grain
    - sls: splunk.deployment_client
    - require:
      - salt: server_setup