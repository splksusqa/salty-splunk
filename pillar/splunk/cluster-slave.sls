# cluster-slave specific settings
include:
 - splunk.common

cluster-slave:
  replication_port: 8888

listen_port:
  splunktcp: 9996
  tcp: 9997
  udp: 9998

retention:
  maxTotalDataSizeMB: 25000
  maxWarmDBCount: 15
  maxDataSize: 500

dataset:
  1m: https://s3.amazonaws.com/qasus_data/1m.tgz

app:
  jira: 'https://s3.amazonaws.com/splunk_apps/add-on-for-jira_201.tgz'
  gendata: 'https://s3.amazonaws.com/splunk_apps/gen_data.tgz'
  google_map: 'https://s3.amazonaws.com/splunk_apps/google-maps_113.tgz'
  sideview: 'https://s3.amazonaws.com/splunk_apps/sideview-utils-lgpl_135.tgz'
  sos: 'https://s3.amazonaws.com/splunk_apps/sos-splunk-on-splunk_32.tgz'
  sos_unix_addon: 'https://s3.amazonaws.com/splunk_apps/splunk-on-splunk-sos-add-on-for-unix-and-linux_205.tgz'
  sos_windows_addon: 'https://s3.amazonaws.com/splunk_apps/splunk-on-splunk-sos-add-on-for-windows_233.tgz'
  unix: 'https://s3.amazonaws.com/splunk_apps/splunk-add-on-for-unix-and-linux_503.tgz'
  hadoop_ops: 'https://s3.amazonaws.com/splunk_apps/splunk-app-for-hadoopops_113.zip'
  hadoop_opsaddon: 'https://s3.amazonaws.com/splunk_apps/splunk-technology-add-on-for-hadoopops_111.tgz'
  db_connect: 'https://s3.amazonaws.com/splunk_apps/splunk-db-connect_114.tgz'
  google_app_engine: 'https://s3.amazonaws.com/splunk_apps/splunk-for-google-app-engine_11.tgz'
  palo_alto_networks: 'https://s3.amazonaws.com/splunk_apps/splunk-for-palo-alto-networks_411.tgz'
  hadoop_connect: 'https://s3.amazonaws.com/splunk_apps/splunk-hadoop-connect_122.tgz'


