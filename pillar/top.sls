# You can set custom pillars then use grains to seperate which node
# should apply, by default it apply only pillars in splunk.common to
# all nodes.
#
# e.g.:
# base:
#   'id:*splunk-cluster-master*:
#     - match: grain
#     - splunk-cluster-master
#   '* and not G@id:*splunk-cluster-master*':
#     - match: compound
#     - splunk
#
# then you can set custom configs in splunk-cluster-master.sls,
# e.g.:
# splunk:
#   home: C:\Splunk
#
# then all nodes other than splunk-cluster-master will use default splunk_home
# and the master will use the custom splunk_home in splunk-cluster-master.sls


base:
  '*':
    - splunk.common

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
