# cluster-slave specific settings
include:
 - splunk.common

cluster-slave:
  replication_port: 8888

listen_port:
  splunktcp: 9996
  tcp: 9997
  udp: 9998