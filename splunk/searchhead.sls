include:
  - splunk.common

{% for mgmt in salt['publish.publish']('role:splunk-indexer', 'splunk.get_mgmt_uri', None, 'grain').values() %}
add-peer:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/search/distributed/peers
    - body:
        name: {{ mgmt }}
        remoteUsername: 'admin'
        remotePassword: 'changeme'
{% endfor %}


