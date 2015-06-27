# salt-run state.orch orchestration.shp

nfs_server_setup:
  salt.state:
    - tgt: 'role:nfsserver'
    - highstate: True

shp_search_head_setup:
  salt.state:
    - tgt: 'role:splunk-shp-searchhead'
    - highstate: True
    - require:
      - salt: nfs_server_setup

