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

  'role:splunk-shc-captain':
    - match: grain
    - splunk.shc-captain

  'role:splunk-shc-member':
    - match: grain
    - splunk.shc-member

  'role:splunk-indexer':
    - match: grain
    - splunk.indexer

  'role:splunk-searchhead':
    - match: grain
    - splunk.searchhead

  'role:splunk-universal-fwd':
    - match: grain
    - splunk.universal-fwd

  'role:splunk-heavy-fwd':
    - match: grain
    - splunk.heavy-fwd

  'role:splunk-light-fwd':
    - match: grain
    - splunk.light-fwd


