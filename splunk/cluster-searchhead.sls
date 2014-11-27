include:
  - splunk.common

set-searchhead:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: searchhead
          master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain')[0] }}"
    - require:
      - sls: splunk.common