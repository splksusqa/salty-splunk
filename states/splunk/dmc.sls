include:
  - splunk.common

{% set indexers = salt['publish.publish']('G@role:splunk-* and not G@role:splunk-dmc', 'splunk.get_mgmt_uri', None, 'compound') %}
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

