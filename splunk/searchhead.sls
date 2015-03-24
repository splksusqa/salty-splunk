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

