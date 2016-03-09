master_setup:
  salt.state:
    - tgt: 'role:central-license-master'
    - tgt_type: grain
    - sls: splunk.central_license_master

slave_setup:
  salt.state:
    - tgt: 'role:central-license-slave'
    - tgt_type: grain
    - sls: splunk.central_license_slave
    - require:
      - salt: master_setup