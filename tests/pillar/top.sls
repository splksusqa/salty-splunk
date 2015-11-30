base:
  'role:splunk-cluster-master':
    - match: grain
    - splunk
    - cluster_master

  'role:splunk-cluster-slave':
    - match: grain
    - splunk
    - cluster_slave