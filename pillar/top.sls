base:
  'role:splunk-cluster-master':
    - match: grain
    - indexer_cluster

  'role:splunk-cluster-slave':
    - match: grain
    - indexer_cluster

  'role:splunk-cluster-searchhead':
    - match: grain
    - indexer_cluster

  '*'
    - splunk