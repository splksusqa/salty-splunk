# You can set custom pillars then use grains to seperate which node
# should apply, by default it apply only pillars in splunk.sls to
# all nodes.
#
# e.g.:
# base:
#   'G@id:*splunk-cluster-master*:
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
    - splunk

