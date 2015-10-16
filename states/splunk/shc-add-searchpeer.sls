{% set master = salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain') %}
{% if master %}
set-cluster-searchhead:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: searchhead
          master_uri: "{{ master.values()[0]  }}"
    - restart_splunk: True
{% endif %}

{% set indexers = salt['publish.publish']('role:splunk-indexer', 'splunk.get_mgmt_uri', None, 'grain') %}
{% if indexers %}
  {% for idx in indexers.values() %}
add-searchpeer-{{ idx }}:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/search/distributed/peers
    - body:
        name: {{ idx }}
        remoteUsername: 'admin'
        remotePassword: 'changeme'
  {% endfor %}
{% endif %}


