# indexer specific settings
include:
  - splunk.common

listen_port:
  splunktcp: 9996
  tcp: 9997
  udp: 9998

retention:
  maxTotalDataSizeMB: 25000
  maxWarmDBCount: 15
  maxDataSize: 500