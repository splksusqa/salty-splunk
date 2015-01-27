base:

  'role:splunk*':
    - schedule
    - splunk.common

  'role:splunk-cluster-master':
    - match: grain
    - splunk.app

  'role:splunk-cluster-searchhead':
    - match: grain
    - splunk.app

  'role:splunk-cluster-slave':
    - match: grain
    - splunk.listen
    - splunk.dataset
    - splunk.app
    - splunk.retention

  'role:splunk-shc-member':
    - match: grain
    - splunk.app
    - splunk.shc-replication

#  'role:splunk-shc-deployer':
#    - match: grain

  'role:splunk-indexer':
    - match: grain
    - splunk.listen
    - splunk.dataset
    - splunk.app
    - splunk.retention

  'role:splunk-searchhead':
    - match: grain
    - splunk.app

  'role:splunk-universal-fwd':
    - match: grain
    - splunk.listen
    - splunk.dataset
    - splunk.app

  'role:splunk-heavy-fwd':
    - match: grain
    - splunk.listen
    - splunk.dataset
    - splunk.app

  'role:splunk-light-fwd':
    - match: grain
    - splunk.listen
    - splunk.dataset
    - splunk.app
