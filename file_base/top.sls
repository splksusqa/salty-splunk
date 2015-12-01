# Using 'id' for now, but better way of specifying nodes is by its 'role'

base:
  'role:splunk-cluster-master':
    - match: grain
    - splunk.cluster_master

  'role:splunk-cluster-slave':
    - match: grain
    - splunk.cluster_slave

  'role:splunk-cluster-searchhead':
    - match: grain
    - splunk.cluster_searchhead

