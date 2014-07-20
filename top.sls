base:

  'id:*splunk-cluster-master*':
    - match: grain
    - splunk.cluster-master

  'id:*splunk-cluster-searchhead*':
    - match: grain
    - splunk.cluster-searchhead

  'id:*splunk-cluster-slave*':
    - match: grain
    - splunk.cluster-slave