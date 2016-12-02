## == splunk global
#version: ""
#listening_ports: 9997
#license_path: salt:// or http://

## == search head cluster
#search_head_cluster:
#  pass4SymmKey: changethis
#  shcluster_label: label
#  replication_factor: 2
#  replication_port: 2
# == indexer cluster
#indexer_cluster:
#  pass4SymmKey: changethis
#  replication_factor: 2
#  search_factor:
#  cluster_label:
#  site_replication_factor:
#  site_search_factor:
#  number_of_sites:
## == universal forwarder
#universal-forwarder:
#  version: 'ember_sustain'
#  listening_ports: 9997


version: "ember_sustain"
listening_ports: 9997

# splunk_home: 'splunk_home'
# license_path: 'license path with salt://'
universal-forwarder:
  version: 'ember_sustain'
  listening_ports: 9997