include:
  - splunk.common

set_retention:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/system/data/indexes/main
    - body:
        maxTotalDataSizeMB: 10000
        maxWarmDBCount: 15
        maxDataSize: 500
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
