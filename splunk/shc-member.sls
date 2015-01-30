include:
 - splunk.common

{% set deployer = salt['publish.publish']('role:splunk-shc-deployer', 'splunk.get_mgmt_uri', None, 'grain') %}

set-shc:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        replication_port://{{ pillar['shc-replication']['port'] }}: {}
        shclustering:
          {% if deployer %}
          conf_deploy_fetch_url: {{ deployer.values()[0] }}
          {% endif %}
          disabled: '0'
          mgmt_uri: https://{{ grains['host']}}:{{ pillar['splunk']['splunkd_port'] }}
          pass4SymmKey: 'pass'
    - restart_splunk: True

