base:

  '*':
    - schedule
    - system
    - s3
    - nfs
    - splunk.common

  'role:splunk-cluster-master':
    - match: grain
    - splunk.common
    - splunk.app

  'role:splunk-cluster-searchhead':
    - match: grain
    - splunk.common
    - splunk.app

  'role:splunk-cluster-slave':
    - match: grain
    - splunk.common
    - splunk.listen
    - splunk.dataset
    - splunk.app
    - splunk.retention
    - splunk.idx-replication

  'role:splunk-shc-member':
    - match: grain
    - splunk.common
    - splunk.app
    - splunk.shc-replication

  'role:splunk-shc-deployer':
    - match: grain
    - splunk.common
    - splunk.app

  'role:splunk-indexer':
    - match: grain
    - splunk.common
    - splunk.listen
    - splunk.dataset
    - splunk.app
    - splunk.retention

  'role:splunk-searchhead':
    - match: grain
    - splunk.common
    - splunk.app

  'role:splunk-universal-fwd':
    - match: grain
    - splunk.common
    - splunk.listen
    - splunk.dataset
    - splunk.app

  'role:splunk-heavy-fwd':
    - match: grain
    - splunk.common
    - splunk.retention
    - splunk.listen
    - splunk.dataset
    - splunk.app

  'role:splunk-light-fwd':
    - match: grain
    - splunk.common
    - splunk.listen
    - splunk.dataset
    - splunk.app

  'role:splunk-dmc':
    - match: grain
    - splunk.common
    - splunk.app

  'role:splunk-lic-master':
    - match: grain
    - splunk.common
    - splunk.app

  'role:splunk-deployment-server':
    - match: grain
    - splunk.common
    - splunk.app