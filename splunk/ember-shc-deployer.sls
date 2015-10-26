include:
  - splunk.common

# add indexers as search peers for DMC
{% set indexers = salt['publish.publish']('role:splunk-ember-indexer', 'splunk.get_mgmt_uri', None, 'grain') %}
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

# add SHs as peers for DMC
{% set indexers = salt['publish.publish']('role:splunk-ember-searchhead', 'splunk.get_mgmt_uri', None, 'grain') %}
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