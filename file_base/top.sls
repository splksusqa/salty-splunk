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

  'role:splunk-shcluster-captain':
    - match: grain
    - splunk.shcluster_captain

  'role:splunk-shcluster-deployer':
    - match: grain
    - splunk.shcluster_deployer

  role:splunk-shcluster-member:
    - match: grain
    - splunk.shcluster_member

  role:splunk-deployment-server:
    - match: grain
    - splunk.indexer

  role:splunk-deployment-client:
    - match: grain
    - splunk.deployment_client

