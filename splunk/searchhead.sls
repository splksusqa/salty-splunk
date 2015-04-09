include:
  - splunk.common

# add search peers and fwd_server
{% set indexers = salt['publish.publish']('role:splunk-indexer', 'splunk.get_mgmt_uri', None, 'grain') %}
{% if indexers %}
  {% for host,uri in indexers.iteritems() %}

add-searchpeer-{{ host }}:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/search/distributed/peers
    - body:
        name: {{ uri }}
        # TODO: update them to the passwd and username of peers, not hardcoded
        remoteUsername: 'admin'
        remotePassword: 'changeme'

  {% endfor %}
{% endif %}

{% set receivers = salt['publish.publish']('role:splunk-indexer', 'splunk.get_listening_uri', 'type=splunktcp', 'grain') %}
{% if receivers %}
  {% for host, uri in receivers.iteritems() %}
set_fwd_server_{{ host }}:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/data/outputs/tcp/server
    - body:
        name: {{ uri }}
    - require:
      - sls: splunk.common

  {% endfor %}
{% endif %}

