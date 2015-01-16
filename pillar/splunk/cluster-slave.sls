# cluster-slave specific settings
include:
  - splunk.common
  - splunk.app
  - splunk.dataset
  - splunk.retention
  - splunk.listen

cluster-slave:
  replication_port: 8888
