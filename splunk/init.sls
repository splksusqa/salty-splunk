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

  'id:*splunk-searchhead*':
    - match: grain
    - splunk.searchhead

  'id:*splunk-indexer*':
    - match: grain
    - splunk.indexer
