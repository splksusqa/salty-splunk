# salt-run state.orch orchestration.shp

nfs_server_setup:
  salt.state:
    - tgt: 'role:nfsserver'
    - tgt_type: grain
    - highstate: True

shp_search_init_folder_setup:
  salt.state:
    - tgt: 'role:splunk-shp-init-folder'
    - tgt_type: grain
    - highstate: True
    - require:
      - salt: nfs_server_setup

shp_search_head_setup:
  salt.state:
    - tgt: 'role:splunk-shp-searchhead'
    - tgt_type: grain
    - highstate: True
    - require:
      - salt: shp_search_init_folder_setup

