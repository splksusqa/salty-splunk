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

  'role:splunk-shcluster-deployer':
    - match: grain
    - searchhead_cluster

  'role:splunk-shcluster-member':
    - match: grain
    - searchhead_cluster

  'role:splunk-shcluster-captain':
    - match: grain
    - searchhead_cluster

  '*':
    - splunk