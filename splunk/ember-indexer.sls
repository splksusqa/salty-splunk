include:
  - splunk.common


set_retention:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/system/data/indexes/main
    - body:
        maxTotalDataSizeMB: {{ pillar['retention']['maxTotalDataSizeMB'] }}
        maxWarmDBCount:     {{ pillar['retention']['maxWarmDBCount'] }}
        maxDataSize:        {{ pillar['retention']['maxDataSize'] }}
    - require:
      - sls: splunk.common


listen_splunktcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/cooked
    - body:
        name: {{ pillar['listen_port']['splunktcp'] }}
    - require:
      - sls: splunk.common


listen_tcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/raw
    - body:
        name: {{ pillar['listen_port']['tcp'] }}
    - require:
      - sls: splunk.common


listen_udp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/udp
    - body:
        name: {{ pillar['listen_port']['udp'] }}
    - require:
      - sls: splunk.common


data:
  splunk:
    - data_monitored
    - source: {{ pillar['dataset']['1m'] }}
    - require:
      - sls: splunk.common



{% set deployment_server = salt['publish.publish']('role:splunk-deployment-server', 'splunk.get_mgmt_uri', 'scheme=False', 'grain') %}
{% if deployment_server %}
set_deployment_server:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/admin/deploymentclient/config
    - body:
        targetUri: "{{ deployment_server.values()[0] }}"
    - require:
      - sls: splunk.common
{% endif %}