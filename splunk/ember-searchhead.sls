include:
  - splunk.common

# add search peers
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




{% set deployment_server = salt['publish.publish']('role:splunk-deployment-server', 'splunk.get_mgmt_uri', 'scheme=False', 'grain') %}
{% if deployment_server %}
set_deployment_server:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/admin/deploymentclient/config
    - body:
        targetUri: "{{ deployment_server.values()[0] }}"
    - require:
      - sls: splunk.common
{% endif %}