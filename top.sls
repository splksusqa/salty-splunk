base:

  'id:*splunk-cluster-master*':
    - match: grain
    - splunk.cluster-master

  'id:*splunk-cluster-searchhead*':
    - match: grain
    - splunk.cluster-searchhead
    - require:
      - sls: splunk.cluster-master

  'id:*splunk-cluster-slave*':
    - match: grain
    - splunk.cluster-slave
    - require:
      - sls: splunk.cluster-master