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
      - splunk: install-splunk
