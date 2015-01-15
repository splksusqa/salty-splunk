# You can set custom pillars then use grains to seperate which node
# should apply, by default it apply only pillars in splunk.common to
# all nodes.
#
# e.g.:
# base:

#   'id:splunk-cluster-slave-01':
#     - match: grain
#     - splunk.cluster-slave-01
#   'G@role:splunk-cluster-slave and not G@id:splunk-cluster-slave-01:
#     - match: compound
#     - splunk.cluster-slave
#
# then you can set custom configs in splunk/cluster-slave-01.sls,
# e.g.:
# splunk:
#   home: C:\Splunk
#
# then all slaves other than splunk-cluster-slave-01 will use default
# splunk_home and slave-01 will use the custom splunk_home in
# splunk.cluster-slave-01.sls


base:
  '*':
    - schedule
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

  'role:splunk-shc-deployer:
    - match: grain
    - splunk.shc-deployer

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

