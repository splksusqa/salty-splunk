# salt-run state.orch orchestration.dist

dist-idx:
  salt.state:
    - tgt: 'role:splunk-indexer'
    - tgt_type: grain
    - sls: splunk.indexer

dist-sh:
  salt.state:
    - tgt: 'role:splunk-searchhead'
    - tgt_type: grain
    - sls: splunk.searchhead
    - require:
      - salt: dist-idx