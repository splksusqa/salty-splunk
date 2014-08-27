# Using 'id' for now, but better way of specifying nodes is by its 'role'

base:

#  'role:splunk*':
#    - match: grain
#    - splunk.common

  'role:splunk-cluster-master':
    - match: grain
    - splunk.cluster-master

  'role:splunk-cluster-searchhead':
    - match: grain
    - splunk.cluster-searchhead

  'role:splunk-cluster-slave':
    - match: grain
    - splunk.cluster-slave

  'role:splunk-indexer':
    - match: grain
    - splunk.indexer

  'role:splunk-searchhead':
    - match: grain
    - splunk.searchhead

  'role:splunk-universal-forwarder':
    - match: grain
    - splunk.universal-forwarder

  'role:splunk-heavy-forwarder':
    - match: grain
    - splunk.heavy-forwarder

  'role:splunk-light-forwarder':
    - match: grain
    - splunk.light-forwarder


