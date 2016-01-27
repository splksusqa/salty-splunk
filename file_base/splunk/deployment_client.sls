include:
  - splunk.indexer

config_client:
  splunk:
    - deployment_client_configured
    # - server: "{{ salt['publish.publish']('role:splunk-deployment-server', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
  require:
    - sls: splunk.indexer
